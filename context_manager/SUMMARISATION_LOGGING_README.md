# Summarisation Logging

This system logs all summarisation events in a structured folder hierarchy to help you understand and debug how conversation summarisation works during the agentic loop.

## Folder Structure

```
logs/summarisation/
├── invocation_001/
│   ├── cycle_001/
│   │   ├── original_prompt.json       # Messages before summarisation check
│   │   ├── no_summarisation.txt       # Created if threshold not exceeded
│   │   └── metadata.json              # Cycle statistics
│   ├── cycle_002/
│   │   ├── original_prompt.json       # Messages before summarisation
│   │   ├── summarised_prompt.json     # Messages after summarisation
│   │   └── metadata.json              # Cycle statistics
│   ├── cycle_003/
│   │   └── ...
│   └── invocation_summary.json        # Summary of entire invocation
├── invocation_002/
│   └── ...
```

## File Descriptions

### Per-Cycle Files

#### `original_prompt.json`
Contains all messages sent to the model BEFORE any summarisation check. This is created for every cycle.

**Structure:**
```json
[
  {
    "role": "user",
    "content": [
      {
        "type": "text",
        "text": "User's message..."
      }
    ]
  },
  {
    "role": "assistant",
    "content": [
      {
        "type": "tool_use",
        "name": "shell",
        "input": {...}
      }
    ]
  }
]
```

#### `summarised_prompt.json`
Contains the messages AFTER summarisation. Only created when summarisation actually occurred (i.e., when token threshold was exceeded).

**Structure:** Same as `original_prompt.json`

#### `no_summarisation.txt`
A simple text file created when NO summarisation occurred (threshold not exceeded). This helps you quickly identify cycles where the context was small enough.

#### `metadata.json`
Statistics and information about the cycle.

**Structure:**
```json
{
  "timestamp": "2025-10-27T14:30:45.123456",
  "cycle_number": 2,
  "invocation": "invocation_001",
  "summarisation_occurred": true,
  "original_message_count": 45,
  "original_token_estimate": 15073,
  "summarised_message_count": 38,
  "summarised_token_estimate": 10500,
  "messages_removed": 7,
  "tokens_saved": 4573,
  "threshold_exceeded": true,
  "token_threshold": 100,
  "summary_ratio": 0.3,
  "preserve_recent_messages": 5
}
```

### Per-Invocation Files

#### `invocation_summary.json`
A summary of the entire invocation, created at the end.

**Structure:**
```json
{
  "invocation": "invocation_001",
  "total_cycles": 15,
  "timestamp": "2025-10-27T14:35:22.654321",
  "cycles_with_summarisation": 3,
  "cycles_without_summarisation": 12,
  "total_summarisations_in_invocation": 3,
  "token_threshold": 100
}
```

## Understanding the Flow

### Invocation
An **invocation** represents one complete call to the agent (one API request to `/invoke`). Each invocation gets a unique directory.

### Cycle
A **cycle** represents one iteration of the agentic loop, specifically one call to the model. During a single invocation, the agent may call the model multiple times (once to decide which tool to use, once after each tool execution, etc.).

**Example flow:**
1. User sends request → **Invocation 1 starts**
2. Agent calls model to decide first action → **Cycle 1**
3. Agent executes tool → (no cycle)
4. Agent calls model to decide next action → **Cycle 2**
5. Agent executes another tool → (no cycle)
6. Agent calls model for final response → **Cycle 3**
7. Response returned to user → **Invocation 1 ends**

## Usage

### Enable/Disable Logging

```python
from context_manager.summarisation_hooks import ProactiveSummarisationHooks

# With logging enabled (default)
hooks = ProactiveSummarisationHooks(
    token_threshold=50000,
    enable_logging=True,  # Creates structured logs
    verbose=True
)

# With logging disabled
hooks = ProactiveSummarisationHooks(
    token_threshold=50000,
    enable_logging=False,  # No log files created
    verbose=True  # Still prints to console
)
```

### Analysing Logs

#### Check how many summarisations occurred
```bash
# Count summarised_prompt.json files
find logs/summarisation -name "summarised_prompt.json" | wc -l

# Count no_summarisation.txt files
find logs/summarisation -name "no_summarisation.txt" | wc -l
```

#### View all invocation summaries
```bash
find logs/summarisation -name "invocation_summary.json" -exec cat {} \;
```

#### Compare original vs summarised prompts
```bash
# View original
cat logs/summarisation/invocation_001/cycle_002/original_prompt.json

# View summarised
cat logs/summarisation/invocation_001/cycle_002/summarised_prompt.json
```

#### Check token savings
```bash
# Extract token savings from all metadata files
find logs/summarisation -name "metadata.json" -exec jq -r 'select(.tokens_saved != null) | "\(.cycle_number): \(.tokens_saved) tokens saved"' {} \;
```

## Benefits

1. **Debugging**: See exactly what messages were sent before and after summarisation
2. **Optimisation**: Analyse token savings to tune your threshold and summary_ratio
3. **Transparency**: Understand when and why summarisation triggers
4. **Comparison**: Compare original context vs summarised context to verify quality
5. **Audit Trail**: Complete history of all summarisation events

## Notes

- Logs can grow large quickly with low thresholds. Consider setting `enable_logging=False` in production if not needed.
- Each cycle creates a copy of all messages, so disk usage can be significant.
- Use `.gitignore` to exclude `logs/summarisation/` from version control.
