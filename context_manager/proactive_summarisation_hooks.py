"""
Proactive summarisation using Strands' built-in logic with BeforeModelCallEvent hooks.

This implementation:
- Reuses Strands' SummarizingConversationManager methods (tool pair protection, etc.)
- Triggers proactively via BeforeModelCallEvent instead of waiting for overflow
- Maintains token threshold control
- Provides structured logging
"""

from typing import TYPE_CHECKING, Optional
from strands.hooks import HookProvider, HookRegistry
from strands.hooks.events import BeforeModelCallEvent, BeforeInvocationEvent, AfterInvocationEvent
from strands.agent.conversation_manager import SummarizingConversationManager
from strands.types.content import Messages
from .summarisation_logger import SummarisationLogger
from .token_counter import TokenCounter
import logging
import copy

if TYPE_CHECKING:
    from strands import Agent

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProactiveSummarisationHooks(HookProvider):
    """
    Hook provider that triggers Strands' summarisation logic proactively
    BEFORE model calls based on token threshold.

    This wraps SummarizingConversationManager and calls its reduce_context()
    method when tokens exceed threshold, rather than waiting for overflow.

    Benefits:
    - Reuses Strands' battle-tested summarisation logic
    - Tool pair protection (doesn't split tool use/result pairs)
    - Summary message persistence
    - Proactive triggering for cost/performance optimization
    """

    def __init__(
        self,
        token_threshold: int = 100000,
        summary_ratio: float = 0.3,
        preserve_recent_messages: int = 10,
        summarization_agent: Optional["Agent"] = None,
        summarization_system_prompt: Optional[str] = None,
        verbose: bool = True,
        enable_logging: bool = True,
    ):
        """
        Initialize proactive summarisation hooks.

        Args:
            token_threshold: Token count at which to trigger summarisation (default: 100K)
            summary_ratio: Ratio of messages to summarise (0.1-0.8, default: 0.3)
            preserve_recent_messages: Minimum recent messages to keep (default: 10)
            summarization_agent: Optional dedicated agent for summarisation
            summarization_system_prompt: Optional custom system prompt for summarisation
            verbose: Enable verbose console output
            enable_logging: Enable structured file logging
        """
        self.token_threshold = token_threshold
        self.verbose = verbose
        self.enable_logging = enable_logging
        self.summarisation_count = 0

        # Create Strands' SummarizingConversationManager to reuse its logic
        self.summarizer = SummarizingConversationManager(
            summary_ratio=summary_ratio,
            preserve_recent_messages=preserve_recent_messages,
            summarization_agent=summarization_agent,
            summarization_system_prompt=summarization_system_prompt,
        )

        # Initialize accurate token counter
        self.token_counter = TokenCounter()
        if self.verbose:
            counter_info = self.token_counter.get_info()
            logger.info(f"Token counter initialised: {counter_info['tokenizer_type']} "
                       f"({'accurate' if counter_info['is_accurate'] else 'estimated'})")

        # Logger for structured logging
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
        Uses Strands' reduce_context() method for the actual summarisation.
        """
        agent = event.agent

        # Count tokens
        current_tokens = self.token_counter.count_tokens(agent.messages)
        message_count = len(agent.messages)

        if self.verbose:
            print(f"🔍 [BeforeModelCall Hook] Tokens: {current_tokens}/{self.token_threshold}, Messages: {message_count}")

        # Make a copy of original messages for logging
        original_messages = copy.deepcopy(agent.messages) if self.enable_logging else None

        # Check if threshold exceeded
        if current_tokens > self.token_threshold:
            if self.verbose:
                print(f"⚠️  [Hook] Token threshold EXCEEDED! Triggering summarisation...")
                print(f"📦 Messages before summarisation: {message_count}")

            try:
                # Use Strands' reduce_context method (with tool pair protection, etc.)
                self.summarizer.reduce_context(agent)

                # Count after summarisation
                messages_after = len(agent.messages)
                tokens_after = self.token_counter.count_tokens(agent.messages)

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
                            "summary_ratio": self.summarizer.summary_ratio,
                            "preserve_recent_messages": self.summarizer.preserve_recent_messages,
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
                self.summarisation_logger.log_cycle(
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
                "summary_ratio": self.summarizer.summary_ratio,
                "preserve_recent_messages": self.summarizer.preserve_recent_messages,
            })
            if self.verbose and summary_file:
                print(f"📊 [Invocation] Summary saved to: {summary_file}")

    # Removed _estimate_token_count() - now using TokenCounter class

    def get_stats(self) -> dict:
        """Get summarisation statistics."""
        return {
            "total_summarisations": self.summarisation_count,
            "token_threshold": self.token_threshold,
            "summary_ratio": self.summarizer.summary_ratio,
            "preserve_recent_messages": self.summarizer.preserve_recent_messages,
            "removed_message_count": self.summarizer.removed_message_count,
        }
