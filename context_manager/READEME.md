High-Level Context Manager System Overview

  The Problem It Solves

  In long-running agent conversations, context accumulates indefinitely:
  Turn 1: User prompt + Agent response           (500 tokens)
  Turn 2: + New prompt + Agent response          (1,200 tokens)
  Turn 3: + Another prompt + Agent response      (2,100 tokens)
  ...
  Turn 20: + Prompt + Response                   (25,000+ tokens) ❌ OVERFLOW

  The Solution Architecture

  1. Hierarchical Memory System

  ┌─────────────────┐
  │  Working Memory │  ← Recent 10-15 actions (immediate context)
  │   (Hot Cache)   │
  ├─────────────────┤
  │ Short-term      │  ← Compressed summaries of older actions
  │ Summary         │
  ├─────────────────┤
  │ Long-term       │  ← Goals, decisions, patterns (persistent)
  │ Memory          │
  └─────────────────┘

  2. Smart Compression Engine

  When memory gets full (70% threshold):
  ┌──────────────────────────────────────┐
  │ 15 Actions in Working Memory         │
  ├──────────────────────────────────────┤
  │ ✅ Keep: Last 5 (always recent)      │
  │ ✅ Keep: High importance (>0.7)      │
  │ 🗜️ Compress: Medium importance       │
  │ 🗑️ Drop: Low importance              │
  └──────────────────────────────────────┘
  Result: 8-10 actions remain + summary

  Core Components

  ActionRecord - Individual Memory Unit

  ActionRecord:
    - timestamp: When it happened
    - action_type: "user_prompt" | "tool_call" | "reasoning" | "decision" | "error"
    - content: What happened (text)
    - success: Did it work?
    - importance: 0.1-1.0 (how critical to keep)
    - token_count: Size estimation

  ContextState - Current Memory State

  ContextState:
    - working_memory: List[ActionRecord]     # Recent actions
    - short_term_summary: str               # Compressed history
    - decision_trail: List[Decision]        # Key choices made
    - error_patterns: Dict[error, count]    # Learning from failures
    - goal_state: Dict                      # Overall objectives
    - current_phase: str                    # What stage we're in

  ContextManager - The Brain

  ContextManager:
    + add_action()           # Record new events
    + _calculate_importance() # Score how critical each action is
    + _compress_memory()     # Intelligent summarisation
    + get_context_for_agent() # Generate prompt context
    + track_error_pattern()  # Learn from failures
    + log_decision()         # Remember key choices

  How It Works Step-by-Step

  1. Action Recording

  User: "Implement authentication"
  ↓
  Manager.add_action("user_prompt", "Implement authentication", success=True)
  ↓
  Calculates importance: 0.9 (user requests are high priority)
  ↓
  Adds to working_memory[0]

  2. Importance Scoring

  def _calculate_importance(content, action_type, success):
      base_scores = {
          'decision': 0.9,      # Architectural choices
          'error': 0.8,         # Learning opportunities  
          'reasoning': 0.7,     # Thought processes
          'tool_call': 0.5,     # Actions taken
          'observation': 0.4    # Results
      }

      # Boost errors (learning)
      if not success: base_score += 0.3

      # Pattern matching
      if "successfully" in content: base_score -= 0.2  # Routine success
      if "Error:" in content: base_score += 0.4        # Important failure

  3. Compression Process

  When working_memory reaches 15 actions:

  Step 1: Categorise by importance
  ├─ Critical (>0.7): Keep all
  ├─ Recent (last 5): Keep all  
  └─ Compressible (middle, low importance): Summarise

  Step 2: Create intelligent summary
  "[COMPRESSED 6 actions]: Executed 4 tools (3 successful); 
  Made 2 decisions: use JWT tokens; implement bcrypt"

  Step 3: Rebuild working memory
  ├─ Recent actions (5)
  ├─ Critical actions (3) 
  └─ Summary replaces 6 actions
  Result: 8 actions + summary

  4. Context Generation for Agent

  def get_context_for_agent():
      context = []

      # Always include current goal
      if goal_state:
          context.append(f"GOAL: {main_goal}")

      # Include compressed history
      if short_term_summary:
          context.append(f"PREVIOUS: {summary}")

      # Include recent actions
      for action in working_memory[-5:]:
          context.append(f"[{action.type}] {action.content}")

      # Include key decisions
      for decision in decision_trail[-3:]:
          context.append(f"DECISION: {decision}")

      return "\n".join(context)

  Intelligence Features

  Error Pattern Learning

  track_error_pattern("File not found: config.py")
  track_error_pattern("File not found: settings.py")
  track_error_pattern("File not found: config.py")  # Same again!

  Result: Creates alert "Recurring pattern: file not found errors"

  Decision Preservation

  log_decision(
      decision="Use JWT tokens for authentication",
      rationale="Stateless, secure, industry standard",
      impact="high"
  )

  # This decision will survive compression cycles

  Phase-Aware Context

  set_phase("exploration")    # Keep discovery patterns
  set_phase("implementation") # Focus on code changes  
  set_phase("debugging")      # Preserve error patterns
  set_phase("review")         # Maintain quality checks

  Integration with Agent

  ContextAwareAgent Wrapper

  class ContextAwareAgent:
      def __call__(self, prompt):
          # 1. Record the user prompt
          context_manager.add_action("user_prompt", prompt)

          # 2. Generate enhanced prompt with context
          enhanced_prompt = self._add_context(prompt)

          # 3. Execute base agent
          result = base_agent(enhanced_prompt)

          # 4. Process and record the result
          context_manager.add_action("agent_response", result)

          # 5. Extract decisions, track errors, etc.
          self._process_result(result)

          return result

  Benefits Achieved

  Token Efficiency

  - Before: Linear growth → context overflow
  - After: Bounded memory with intelligent compression

  Coherent Long-term Tasks

  - Remembers: Goals, decisions, important discoveries
  - Forgets: Routine tool outputs, redundant information
  - Learns: Error patterns, successful approaches

  Adaptive Strategy

  - Exploration: Keep detailed reasoning
  - Implementation: Focus on code changes
  - Debugging: Preserve error patterns
  - Review: Maintain quality metrics

  Real-World Example

  Goal: "Implement user authentication system"

  Action 1: user_prompt "implement auth" (importance: 0.9)
  Action 2: reasoning "need to check existing setup" (0.7)
  Action 3: tool_call "find . -name '*.py'" (0.5)
  Action 4: agent_response "found auth.py" (0.4)
  Action 5: decision "use JWT tokens" (0.9)
  ...
  Action 15: tool_call "pip install bcrypt" (0.3)

  Compression triggered:
  ✅ Keep: Actions 11-15 (recent)
  ✅ Keep: Actions 1,2,5 (high importance)  
  🗜️ Compress: Actions 3,4,6-10 → "Analyzed existing code structure"

  The system maintains coherent understanding while staying within token budgets through intelligent memory management.