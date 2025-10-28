import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
from strands.types.content import Messages


class SummarisationLogger:
    """
    Logs summarisation events with structured folder hierarchy:
    logs/summarisation/invocation_{n}/cycle_{m}/
        - original_prompt.json
        - summarised_prompt.json (if summarisation occurred)
        - metadata.json
    """

    def __init__(self, base_dir: str = "logs/summarisation"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.current_invocation = None
        self.current_invocation_dir = None
        self.cycle_count = 0

    def start_invocation(self) -> str:
        """Start a new invocation and create its directory."""
        # Find the next invocation number
        existing_invocations = [
            d for d in self.base_dir.iterdir()
            if d.is_dir() and d.name.startswith("invocation_")
        ]
        invocation_num = len(existing_invocations) + 1

        self.current_invocation = f"invocation_{invocation_num:03d}"
        self.current_invocation_dir = self.base_dir / self.current_invocation
        self.current_invocation_dir.mkdir(exist_ok=True)
        self.cycle_count = 0

        return self.current_invocation

    def log_cycle(
        self,
        original_messages: Messages,
        summarised_messages: Messages = None,
        metadata: Dict[str, Any] = None,
    ) -> Path:
        """
        Log a single cycle (model call) with original and potentially summarised messages.

        Args:
            original_messages: The messages before potential summarisation
            summarised_messages: The messages after summarisation (None if no summarisation occurred)
            metadata: Additional metadata about the cycle
        """
        # Ensure invocation was started (should be called by hook)
        if self.current_invocation_dir is None:
            raise RuntimeError(
                "log_cycle() called before start_invocation(). "
                "Ensure BeforeInvocationEvent hook is registered."
            )

        self.cycle_count += 1
        cycle_dir = self.current_invocation_dir / f"cycle_{self.cycle_count:03d}"
        cycle_dir.mkdir(exist_ok=True)

        # Save original prompt
        original_file = cycle_dir / "original_prompt.json"
        self._save_messages(original_messages, original_file)

        # Save summarised prompt if summarisation occurred
        if summarised_messages is not None:
            summarised_file = cycle_dir / "summarised_prompt.json"
            self._save_messages(summarised_messages, summarised_file)
        else:
            # Create a note that no summarisation occurred
            (cycle_dir / "no_summarisation.txt").write_text(
                "No summarisation occurred in this cycle. "
                "Original prompt was below threshold."
            )

        # Save metadata
        if metadata is None:
            metadata = {}

        metadata.update({
            "timestamp": datetime.now().isoformat(),
            "cycle_number": self.cycle_count,
            "invocation": self.current_invocation,
            "summarisation_occurred": summarised_messages is not None,
            "original_message_count": len(original_messages),
            "original_token_estimate": self._estimate_tokens(original_messages),
        })

        if summarised_messages is not None:
            metadata.update({
                "summarised_message_count": len(summarised_messages),
                "summarised_token_estimate": self._estimate_tokens(summarised_messages),
                "messages_removed": len(original_messages) - len(summarised_messages),
                "tokens_saved": self._estimate_tokens(original_messages) - self._estimate_tokens(summarised_messages),
            })

        metadata_file = cycle_dir / "metadata.json"
        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        return cycle_dir

    def _save_messages(self, messages: Messages, file_path: Path) -> None:
        """Save messages to a JSON file with pretty formatting."""
        # Convert messages to a more readable format
        readable_messages = []
        for msg in messages:
            readable_msg = {
                "role": msg.get("role", "unknown"),
                "content": [],
            }

            content = msg.get("content", [])
            if isinstance(content, list):
                for block in content:
                    if "text" in block:
                        readable_msg["content"].append({
                            "type": "text",
                            "text": block["text"]
                        })
                    elif "toolUse" in block:
                        tool_use = block["toolUse"]
                        readable_msg["content"].append({
                            "type": "tool_use",
                            "name": tool_use.get("name", "unknown"),
                            "input": tool_use.get("input", {})
                        })
                    elif "toolResult" in block:
                        tool_result = block["toolResult"]
                        readable_msg["content"].append({
                            "type": "tool_result",
                            "tool_use_id": tool_result.get("toolUseId", "unknown"),
                            "content": self._extract_tool_result_content(tool_result)
                        })
            elif isinstance(content, str):
                readable_msg["content"].append({
                    "type": "text",
                    "text": content
                })

            readable_messages.append(readable_msg)

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(readable_messages, f, indent=2, ensure_ascii=False)

    def _extract_tool_result_content(self, tool_result: Dict) -> str:
        """Extract readable content from tool result."""
        result_content = tool_result.get("content", [])
        text_parts = []
        for block in result_content:
            if "text" in block:
                text_parts.append(block["text"][:500])  # Limit length
        return "\n".join(text_parts) if text_parts else "No text content"

    def _estimate_tokens(self, messages: Messages) -> int:
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

    def create_invocation_summary(self, additional_info: Dict[str, Any] = None) -> Path:
        """Create a summary file for the current invocation."""
        if self.current_invocation_dir is None:
            return None

        summary = {
            "invocation": self.current_invocation,
            "total_cycles": self.cycle_count,
            "timestamp": datetime.now().isoformat(),
        }

        if additional_info:
            summary.update(additional_info)

        # Count how many cycles had summarisation
        cycles_with_summarisation = 0
        for i in range(1, self.cycle_count + 1):
            cycle_dir = self.current_invocation_dir / f"cycle_{i:03d}"
            if (cycle_dir / "summarised_prompt.json").exists():
                cycles_with_summarisation += 1

        summary["cycles_with_summarisation"] = cycles_with_summarisation
        summary["cycles_without_summarisation"] = self.cycle_count - cycles_with_summarisation

        summary_file = self.current_invocation_dir / "invocation_summary.json"
        with open(summary_file, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        return summary_file

    def get_current_cycle_dir(self) -> Path:
        """Get the directory for the current cycle."""
        if self.current_invocation_dir is None:
            return None
        return self.current_invocation_dir / f"cycle_{self.cycle_count:03d}"
