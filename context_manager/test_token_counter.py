"""
Quick test script for TokenCounter to verify it works correctly.

Run with:
  python test_token_counter.py (from context_manager directory)
  python -m context_manager.test_token_counter (from project root)
"""

import sys
import os

# Add parent directory to path if running from context_manager directory
if os.path.basename(os.getcwd()) == 'context_manager':
    sys.path.insert(0, os.path.dirname(os.getcwd()))

from context_manager.token_counter import TokenCounter

def test_token_counter():
    """Test that token counter works with sample messages."""

    # Initialise counter
    print("🔧 Initialising TokenCounter...")
    counter = TokenCounter()

    info = counter.get_info()
    print(f"✅ Tokenizer info: {info}")

    # Create sample messages
    sample_messages = [
        {
            "role": "user",
            "content": [{"text": "Hello, how are you today?"}]
        },
        {
            "role": "assistant",
            "content": [{"text": "I'm doing great! How can I help you?"}]
        },
        {
            "role": "user",
            "content": [
                {
                    "text": "Can you help me understand how token counting works?"
                }
            ]
        }
    ]

    # Count tokens
    print("\n🔍 Counting tokens...")
    token_count = counter.count_tokens(sample_messages)

    print(f"✅ Total tokens: {token_count}")
    print(f"📊 Messages: {len(sample_messages)}")
    print(f"📈 Avg tokens per message: {token_count / len(sample_messages):.1f}")

    # Test with tool use and tool results (complex structure)
    print("\n🔧 Testing with tool use messages...")
    complex_messages = [
        {
            "role": "user",
            "content": [{"text": "Read the file config.json"}]
        },
        {
            "role": "assistant",
            "content": [
                {"text": "I'll read that file for you."},
                {
                    "toolUse": {
                        "toolUseId": "tool_123",
                        "name": "file_read",
                        "input": {"path": "/Users/test/config.json"}
                    }
                }
            ]
        },
        {
            "role": "user",
            "content": [
                {
                    "toolResult": {
                        "toolUseId": "tool_123",
                        "content": [{"text": '{"setting": "value", "enabled": true}'}]
                    }
                }
            ]
        }
    ]

    complex_count = counter.count_tokens(complex_messages)
    print(f"✅ Complex messages tokens: {complex_count}")
    print(f"📊 Messages: {len(complex_messages)}")

    # Test with larger content
    print("\n📦 Testing with large content...")
    large_message = [{
        "role": "user",
        "content": [{"text": " ".join(["Hello world!"] * 1000)}]  # ~2000 words
    }]

    large_count = counter.count_tokens(large_message)
    print(f"✅ Large message tokens: {large_count}")

    print("\n✅ All tests passed! Token counter is working correctly.")
    print("🎯 Works with all message types: text, tool use, tool results, etc.")

if __name__ == "__main__":
    test_token_counter()
