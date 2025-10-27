from typing import TYPE_CHECKING
from strands.hooks import HookProvider, HookRegistry
from strands.hooks.events import BeforeModelCallEvent, BeforeInvocationEvent, AfterInvocationEvent
from strands.types.content import Messages
from .summarisation_logger import SummarisationLogger
import logging
import copy

if TYPE_CHECKING:
    from strands import Agent

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProactiveSummarisationHooks(HookProvider):
    """
    Hook provider that triggers summarisation BEFORE each model call
    during the agentic loop, based on token threshold.

    Uses BeforeModelCallEvent which fires right before the model is called,
    allowing us to reduce context before it's sent to the LLM.

    Logs all summarisation events in a structured format:
    logs/summarisation/invocation_{n}/cycle_{m}/
    """

    def __init__(
        self,
        token_threshold: int = 50000, # Summarise when reaching 50k tokens (good balance for production)
        summary_ratio: float = 0.4,    # Summarise 40% of messages (more aggressive)
        preserve_recent_messages: int = 10,  # Always keep last 10 messages (recent context important)
        summarisation_system_prompt: str = None,
        verbose: bool = True,
        enable_logging: bool = True,
    ):
        self.token_threshold = token_threshold
        self.summary_ratio = summary_ratio
        self.preserve_recent_messages = preserve_recent_messages
        self.summarisation_system_prompt = summarisation_system_prompt or (
            "You are an expert assistant that summarises conversations concisely."
        )
        self.verbose = verbose
        self.enable_logging = enable_logging
        self.summarisation_count = 0
        self.summarisation_logger = SummarisationLogger() if enable_logging else None

    def register_hooks(self, registry: HookRegistry) -> None:
        """Register hooks for lifecycle and model call events."""
        registry.add_callback(BeforeInvocationEvent, self.on_invocation_start)
        registry.add_callback(BeforeModelCallEvent, self.check_and_summarise_before_model_call)
        registry.add_callback(AfterInvocationEvent, self.on_invocation_end)

    def on_invocation_start(self, event: BeforeInvocationEvent) -> None:
        """Called at the start of each agent invocation."""
        if self.enable_logging and self.summarisation_logger:
            invocation_id = self.summarisation_logger.start_invocation()
            if self.verbose:
                print(f"🆕 [Invocation] Started {invocation_id}")

    def check_and_summarise_before_model_call(self, event: BeforeModelCallEvent) -> None:
        """
        Called BEFORE each model call to check if summarisation is needed.
        This fires during the agentic loop, before the agent calls the model.
        """
        agent = event.agent

        # Estimate token count
        current_tokens = self._estimate_token_count(agent.messages)
        message_count = len(agent.messages)

        if self.verbose:
            print(f"🔍 [BeforeModelCall Hook] Tokens: {current_tokens}/{self.token_threshold}, Messages: {message_count}")

        # Make a copy of original messages for logging
        original_messages = copy.deepcopy(agent.messages) if self.enable_logging else None

        # Check if threshold exceeded
        summarisation_occurred = current_tokens > self.token_threshold

        if summarisation_occurred:
            if self.verbose:
                print(f"⚠️  [Hook] Token threshold EXCEEDED! Summarising before model call...")
                print(f"📦 Messages before summarisation: {message_count}")

            try:
                self._proactive_summarise(agent)

                # Count after summarisation
                messages_after = len(agent.messages)
                tokens_after = self._estimate_token_count(agent.messages)

                self.summarisation_count += 1

                if self.verbose:
                    print(f"✅ [Hook] SUMMARISATION COMPLETED BEFORE MODEL CALL!")
                    print(f"📦 Messages after summarisation: {messages_after}")
                    print(f"📊 Tokens after summarisation: {tokens_after}")
                    print(f"💾 Tokens saved: {current_tokens - tokens_after}")
                    print(f"🔄 Total summarisations: {self.summarisation_count}")
                    print("-" * 60)

                # Log the cycle with summarisation
                if self.enable_logging and self.summarisation_logger:
                    cycle_dir = self.summarisation_logger.log_cycle(
                        original_messages=original_messages,
                        summarised_messages=agent.messages,
                        metadata={
                            "threshold_exceeded": True,
                            "token_threshold": self.token_threshold,
                            "summary_ratio": self.summary_ratio,
                            "preserve_recent_messages": self.preserve_recent_messages,
                        }
                    )
                    if self.verbose:
                        print(f"📁 Logged to: {cycle_dir}")

            except Exception as e:
                if self.verbose:
                    logger.error(f"❌ [Hook] Summarisation failed: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
        else:
            # No summarisation needed, but still log the cycle
            if self.enable_logging and self.summarisation_logger:
                cycle_dir = self.summarisation_logger.log_cycle(
                    original_messages=original_messages,
                    summarised_messages=None,  # No summarisation
                    metadata={
                        "threshold_exceeded": False,
                        "token_threshold": self.token_threshold,
                    }
                )

    def on_invocation_end(self, event: AfterInvocationEvent) -> None:
        """Called at the end of each agent invocation."""
        if self.enable_logging and self.summarisation_logger:
            summary_file = self.summarisation_logger.create_invocation_summary({
                "total_summarisations_in_invocation": self.summarisation_count,
                "token_threshold": self.token_threshold,
            })
            if self.verbose and summary_file:
                print(f"📊 [Invocation] Summary saved to: {summary_file}")

    def _proactive_summarise(self, agent: "Agent") -> None:
        """
        Proactively summarise older messages when token threshold is exceeded.
        """
        if len(agent.messages) <= self.preserve_recent_messages:
            if self.verbose:
                logger.warning(
                    f"⚠️  Not enough messages to summarise "
                    f"(have {len(agent.messages)}, need > {self.preserve_recent_messages})"
                )
            return

        # Calculate how many messages to summarise
        num_to_summarise = int(len(agent.messages) * self.summary_ratio)

        # Ensure we don't summarise too many (leave at least preserve_recent_messages)
        max_summarisable = len(agent.messages) - self.preserve_recent_messages
        num_to_summarise = min(num_to_summarise, max_summarisable)

        if num_to_summarise < 1:
            if self.verbose:
                logger.warning(
                    f"⚠️  Cannot summarise (would leave fewer than {self.preserve_recent_messages} messages)"
                )
            return

        if self.verbose:
            print(f"📝 [Hook] Summarising {num_to_summarise} messages out of {len(agent.messages)}")

        # Split messages: older ones to summarise, recent ones to preserve
        messages_to_summarise = agent.messages[:num_to_summarise]
        messages_to_preserve = agent.messages[num_to_summarise:]

        # Create summary prompt
        summary_prompt = self._create_summary_prompt(messages_to_summarise)

        # Create a temporary agent to generate summary (avoid recursion)
        from strands import Agent
        from strands.agent.conversation_manager import NullConversationManager

        temp_agent = Agent(
            model=agent.model,
            system_prompt=self.summarisation_system_prompt,
            conversation_manager=NullConversationManager(),
        )

        summary_result = temp_agent(summary_prompt)
        summary_text = summary_result.message.get("content", [{}])[0].get("text", "Summary unavailable")

        # Create summary message
        summary_message = {
            "role": "user",
            "content": [{"text": f"[CONVERSATION SUMMARY]\n{summary_text}"}],
        }

        # Replace old messages with summary + preserved messages
        agent.messages = [summary_message] + messages_to_preserve

        if self.verbose:
            print(f"✅ [Hook] Created summary from {num_to_summarise} messages")

    def _create_summary_prompt(self, messages: Messages) -> str:
        """Create a prompt for summarising messages."""
        prompt_parts = ["Please summarise the following conversation concisely, focusing on:\n"]
        prompt_parts.append("- Key topics and decisions\n")
        prompt_parts.append("- Tools used and their purposes\n")
        prompt_parts.append("- Important technical details\n")
        prompt_parts.append("- Any unresolved issues or questions\n\n")
        prompt_parts.append("Conversation to summarise:\n\n")

        for i, message in enumerate(messages):
            role = message.get("role", "unknown")
            content = message.get("content", [])

            prompt_parts.append(f"--- Message {i+1} ({role}) ---\n")

            if isinstance(content, list):
                for block in content:
                    if "text" in block:
                        prompt_parts.append(block["text"][:500])  # Limit text length
                        prompt_parts.append("\n")
                    elif "toolUse" in block:
                        tool_use = block["toolUse"]
                        prompt_parts.append(f"[Tool used: {tool_use.get('name', 'unknown')}]\n")
                    elif "toolResult" in block:
                        prompt_parts.append("[Tool result received]\n")
            elif isinstance(content, str):
                prompt_parts.append(content[:500])
                prompt_parts.append("\n")

            prompt_parts.append("\n")

        return "".join(prompt_parts)

    def _estimate_token_count(self, messages: Messages) -> int:
        """Estimate token count from messages."""
        total_chars = 0

        for message in messages:
            content = message.get("content", [])

            if isinstance(content, list):
                for block in content:
                    if "text" in block:
                        total_chars += len(block["text"])
                    elif "toolUse" in block:
                        total_chars += len(str(block["toolUse"]))
                    elif "toolResult" in block:
                        tool_result = block["toolResult"]
                        result_content = tool_result.get("content", [])
                        for result_block in result_content:
                            if "text" in result_block:
                                total_chars += len(result_block["text"])
                    elif "image" in block:
                        total_chars += 85 * 4
            elif isinstance(content, str):
                total_chars += len(content)

        return total_chars // 4

    def get_stats(self) -> dict:
        """Get summarisation statistics."""
        return {
            "total_summarisations": self.summarisation_count,
            "token_threshold": self.token_threshold,
        }
