# Context Management & Proactive Summarisation

This directory contains implementations for managing conversation context in Strands agents, including proactive summarisation to optimize cost and performance.

## Files Overview

### Production Files (Use These)

1. **`hooks/proactive_summarisation.py`** ⭐ **RECOMMENDED**
   - Hybrid approach combining Strands' battle-tested logic with proactive triggering
   - Reuses `SummarizingConversationManager` methods (tool pair protection, summary reuse)
   - Triggers via `BeforeModelCallEvent` hooks at configurable token threshold
   - **Best of both worlds**: Strands' reliability + proactive cost savings
   - **Class**: `ProactiveSummarisation` (formerly `ProactiveSummarisationHooks`)

2. **`summarisation_logger.py`**
   - Structured logging system for all summarisation events
   - Creates hierarchical logs: `logs/summarisation/invocation_N/cycle_M/`
   - Enables debugging and analysis of summarisation behavior

### Reference/Learning Files

3. **`summarisation_hooks.py`**
   - Original custom implementation (kept for reference)
   - Implements summarisation from scratch without reusing Strands' logic
   - Demonstrates token-aware targeting approach
   - **Not recommended for production** (lacks tool pair protection)

4. **`conversation_manager.py`**
   - Original attempt using ConversationManager approach
   - **Not recommended** (wrong pattern - hooks are the correct approach)

## Architecture Comparison

### Strands Built-in (Reactive)

```python
from strands.agent.conversation_manager import SummarizingConversationManager

agent = Agent(
    conversation_manager=SummarizingConversationManager(
        summary_ratio=0.3,
        preserve_recent_messages=10,
    )
)
```

**How it works:**
- Waits for context overflow exception (~200K tokens)
- Calls `reduce_context()` after the error
- Summarises and retries the model call

**Pros:**
- ✅ Simple, built-in
- ✅ Tool pair protection
- ✅ Summary message reuse

**Cons:**
- ❌ Waits until 200K tokens (expensive!)
- ❌ Reactive, not proactive
- ❌ No visibility/logging

### Proactive Hooks (Recommended)

```python
from hooks.proactive_summarisation import ProactiveSummarisation

hooks = ProactiveSummarisation(
    token_threshold=100000,  # Trigger at 100K tokens
    summary_ratio=0.3,
    preserve_recent_messages=10,
    enable_logging=True,
)

agent = Agent(hooks=[hooks])
```

**How it works:**
- `BeforeModelCallEvent` fires before each model call
- Checks token count against threshold
- Calls Strands' `reduce_context()` proactively if threshold exceeded
- Model call proceeds with reduced context

**Pros:**
- ✅ Proactive (triggers at 100K, not 200K)
- ✅ Cost savings (~50% reduction in tokens processed)
- ✅ Tool pair protection (reuses Strands' logic)
- ✅ Summary message reuse
- ✅ Structured logging
- ✅ Better performance (smaller context = faster)

**Cons:**
- ⚠️  Slightly more complex setup

## Usage

### Basic Setup

In `agent.py`:

```python
USE_PROACTIVE_SUMMARISATION = True  # or False

if USE_PROACTIVE_SUMMARISATION:
    from hooks.proactive_summarisation import ProactiveSummarisation

    summarisation_hooks = ProactiveSummarisation(
        token_threshold=100000,
        summary_ratio=0.3,
        preserve_recent_messages=10,
        verbose=True,
        enable_logging=True,
    )

    agent = Agent(
        system_prompt=system_prompt,
        model=model,
        tools=tools,
        hooks=[summarisation_hooks]
    )
else:
    # Use Strands' default reactive approach
    from strands.agent.conversation_manager import SummarizingConversationManager

    agent = Agent(
        system_prompt=system_prompt,
        model=model,
        tools=tools,
        conversation_manager=SummarizingConversationManager()
    )
```

### Configuration Options

#### `token_threshold` (default: 100000)
When to trigger summarisation. Recommendations:
- **50,000**: Very aggressive, frequent summarisation
- **100,000**: Balanced (50% of Sonnet's 200K limit) ⭐ **RECOMMENDED**
- **150,000**: Conservative, rare summarisation
- **200,000**: Same as reactive (defeats the purpose)

#### `summary_ratio` (default: 0.3)
Percentage of messages to summarise (0.1 - 0.8):
- **0.2**: Light summarisation (20% of messages)
- **0.3**: Balanced ⭐ **RECOMMENDED** (Strands default)
- **0.5**: Aggressive summarisation (50% of messages)

#### `preserve_recent_messages` (default: 10)
Minimum recent messages to always keep:
- **5**: Minimal context
- **10**: Balanced ⭐ **RECOMMENDED**
- **20**: Rich context, less aggressive

#### `enable_logging` (default: True)
Creates structured logs in `logs/summarisation/`:
- **True**: Enable for debugging/analysis ⭐ **RECOMMENDED for dev**
- **False**: Disable in production to save disk space

### Advanced: Custom Summarisation Agent

```python
# Create a dedicated fast model for summarisation
summarization_agent = Agent(
    model=LiteLLMModel(model_id="openai/gpt-4o-mini"),  # Cheaper model
    system_prompt="Create concise bullet-point summaries."
)

summarisation_hooks = ProactiveSummarisation(
    token_threshold=100000,
    summarization_agent=summarization_agent,  # Use dedicated agent
    enable_logging=True,
)
```

### Advanced: Custom System Prompt

```python
custom_prompt = """Create an ultra-concise summary with:
1. Key decisions made
2. Code files modified
3. Open issues
Maximum 5 bullet points."""

summarisation_hooks = ProactiveSummarisation(
    token_threshold=100000,
    summarization_system_prompt=custom_prompt,  # Custom prompt
    enable_logging=True,
)
```

## Logging Structure

When `enable_logging=True`, creates:

```
logs/summarisation/
├── invocation_001/
│   ├── cycle_001/
│   │   ├── original_prompt.json      # Before summarisation
│   │   ├── no_summarisation.txt      # If threshold not exceeded
│   │   └── metadata.json             # Statistics
│   ├── cycle_002/
│   │   ├── original_prompt.json      # Before summarisation
│   │   ├── summarised_prompt.json    # After summarisation
│   │   └── metadata.json
│   └── invocation_summary.json       # Overall stats
```

See [SUMMARISATION_LOGGING_README.md](./SUMMARISATION_LOGGING_README.md) for details.

## Performance Impact

### Cost Savings Example

**Scenario:** 50-tool-use conversation reaching 150K tokens

**Reactive (Strands default):**
- Processes full 150K tokens on every model call
- ~40 model calls × 150K = 6M input tokens
- Cost: ~$6.00 (at $1/M tokens)

**Proactive (100K threshold):**
- Summarises at 100K tokens
- 25 calls × 100K + 15 calls × 70K = 3.55M input tokens
- Cost: ~$3.55 (at $1/M tokens)
- **Savings: 41%** 💰

### Latency Impact

Smaller context = faster model responses:
- 50K tokens: ~2-3s response time
- 100K tokens: ~4-6s response time
- 200K tokens: ~8-12s response time

## Monitoring

### Console Output

With `verbose=True`:

```
🔍 [BeforeModelCall Hook] Tokens: 105000/100000, Messages: 45
⚠️  [Hook] Token threshold EXCEEDED! Triggering summarisation...
📦 Messages before summarisation: 45
✅ [Hook] SUMMARISATION COMPLETED BEFORE MODEL CALL!
📦 Messages after summarisation: 32
📊 Tokens after summarisation: 68000
💾 Tokens saved: 37000
🔄 Total summarisations: 1
```

### Get Statistics

```python
stats = summarisation_hooks.get_stats()
print(stats)
# {
#     'total_summarisations': 3,
#     'token_threshold': 100000,
#     'summary_ratio': 0.3,
#     'preserve_recent_messages': 10,
#     'removed_message_count': 85
# }
```

## When to Use Proactive Summarisation

### ✅ Use Proactive When:
- Long conversations (>50K tokens expected)
- Cost optimization is important
- Performance/latency matters
- You want visibility into summarisation

### ❌ Use Reactive (Default) When:
- Short conversations (<50K tokens)
- Simplicity preferred over optimization
- Cost/performance not concerns
- Testing/prototyping

## Implementation Details

### How Proactive Hooks Work

1. **BeforeInvocationEvent**: Creates new invocation log directory
2. **BeforeModelCallEvent** (fires before each model call):
   - Estimates token count
   - If > threshold: calls `SummarizingConversationManager.reduce_context()`
   - Logs original and summarised messages
3. **AfterInvocationEvent**: Creates invocation summary

### Tool Pair Protection

The implementation ensures tool use/result pairs stay together:

```python
# BAD (would break):
[toolUse, toolResult] | [userMessage, ...]
                     ↑ split here

# GOOD (adjusted):
[toolUse, toolResult, userMessage] | [...]
                                   ↑ split here
```

This is handled automatically by `SummarizingConversationManager._adjust_split_point_for_tool_pairs()`.

### Summary Message Reuse

When multiple summarisations occur:

```
Cycle 1: [msg1, msg2, msg3, msg4, msg5]
         ↓ summarise
Cycle 2: [SUMMARY(1-2), msg3, msg4, msg5, msg6, msg7]
         ↓ summarise
Cycle 3: [SUMMARY(1-4), msg5, msg6, msg7, msg8]
```

The summary message is updated, not duplicated.

## Troubleshooting

### "Summarisation happening every cycle"

**Cause:** Threshold too low or not reducing enough tokens

**Solution:**
```python
# Increase threshold
token_threshold=100000  # not 2000

# Or increase summary ratio
summary_ratio=0.4  # summarise more messages
```

### "Summary longer than original"

**Cause:** Threshold too low, summarising tiny conversations

**Solution:** Use threshold ≥ 50000 tokens

### "No summarisation occurring"

**Cause:** Conversations not reaching threshold

**Solution:** Lower threshold or check token estimation

## References

- [Strands Conversation Management Docs](https://strandsagents.com/latest/documentation/docs/user-guide/concepts/agents/conversation-management/)
- [Strands Hooks API](https://strandsagents.com/latest/documentation/docs/api-reference/hooks/)
- [SummarizingConversationManager Source](/Users/dinindu/Projects/GitHub/sdk-python/src/strands/agent/conversation_manager/summarizing_conversation_manager.py)
