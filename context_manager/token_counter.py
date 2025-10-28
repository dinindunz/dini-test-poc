"""
Token counting using tiktoken (OpenAI's tokenizer).

Note: tiktoken uses cl100k_base encoding which is similar to Claude's tokenisation.
It's accurate enough for context management purposes.
"""

import json
import logging
from typing import Optional
from strands.types.content import Messages

logger = logging.getLogger(__name__)


class TokenCounter:
    """
    Token counter using tiktoken.
    
    """

    def __init__(self):
        """Initialize the token counter with tiktoken."""
        self.tokenizer = None

        # Initialize tiktoken local tokenizer
        self._initialize_tokenizer()

    def _initialize_tokenizer(self) -> None:
        """Initialize tiktoken's local tokenizer."""
        try:
            import tiktoken
            # Use cl100k_base encoding (used by GPT-4, GPT-3.5-turbo, and similar to Claude)
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
            logger.info("✅ tiktoken tokenizer initialized (local, no API calls needed)")
        except ImportError:
            logger.error(
                "❌ tiktoken library not installed! "
                "Install it with: pip install tiktoken"
            )
            raise ImportError(
                "The 'tiktoken' library is required for token counting. "
                "Install it with: pip install tiktoken"
            )

    def count_tokens(self, messages: Messages) -> int:
        """
        Count tokens in a list of messages using tiktoken's tokenizer.

        Args:
            messages: List of message dictionaries in Strands format

        Returns:
            Total token count across all messages
        """
        try:
            # Convert entire messages list to JSON string
            # This is more accurate as it includes all structural overhead
            messages_json = json.dumps(messages)
            tokens = self.tokenizer.encode(messages_json)
            return len(tokens)
        except Exception as e:
            logger.warning(f"Error encoding with tiktoken: {e}, using fallback")
            # Fallback to simple estimation
            return len(str(messages)) // 4

    def get_info(self) -> dict:
        """Get information about the current tokenizer."""
        return {
            "tokenizer_type": "tiktoken (cl100k_base)",
            "is_accurate": True,
            "is_local": True,
            "makes_api_calls": False,
            "requires_api_key": False,
        }


# Singleton instance for convenience
_default_counter: Optional[TokenCounter] = None


def get_token_counter() -> TokenCounter:
    """
    Get or create a token counter instance.

    Returns:
        TokenCounter instance
    """
    global _default_counter

    if _default_counter is None:
        _default_counter = TokenCounter()

    return _default_counter


def count_tokens(messages: Messages) -> int:
    """
    Convenience function to count tokens in messages.

    Args:
        messages: List of message dictionaries

    Returns:
        Total token count
    """
    counter = get_token_counter()
    return counter.count_tokens(messages)
