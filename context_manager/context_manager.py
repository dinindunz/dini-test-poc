"""
Context Window Management System for Agentic Loops

Implements hierarchical memory, smart summarisation, and context rotation
to handle long-running agent tasks efficiently.
"""

import json
import time
import hashlib
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict, field
from pathlib import Path
from collections import deque
import re


@dataclass
class ActionRecord:
    """Record of a single agent action"""
    timestamp: float
    action_type: str  # 'tool_call', 'reasoning', 'observation', 'decision'
    content: str
    success: bool
    token_count: int
    importance: float = 1.0  # 0.1 = can drop, 1.0 = critical
    compressed: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ContextState:
    """Current state of context management"""
    working_memory: List[ActionRecord] = field(default_factory=list)
    short_term_summary: str = ""
    long_term_memory: Dict[str, Any] = field(default_factory=dict)
    current_phase: str = "initialisation"
    goal_state: Dict[str, Any] = field(default_factory=dict)
    decision_trail: List[Dict[str, Any]] = field(default_factory=list)
    error_patterns: Dict[str, int] = field(default_factory=dict)
    success_patterns: List[str] = field(default_factory=list)


class ContextManager:
    """Manages context window for agentic loops"""

    def __init__(self, max_working_memory: int = 10, max_context_tokens: int = 8000):
        self.max_working_memory = max_working_memory
        self.max_context_tokens = max_context_tokens

        self.state = ContextState()
        self.total_actions = 0
        self.compression_threshold = 0.7  # Compress when 70% full
        self._compression_count = 0  # Track compression events

        # Pattern matchers for smart compression
        self.tool_success_patterns = [
            (r"✅.*successfully", 0.3),  # Success messages can be compressed
            (r"File.*created successfully", 0.2),
            (r"Command completed", 0.2),
        ]

        self.error_patterns = [
            (r"❌.*failed", 0.8),  # Errors are important
            (r"Error:", 0.9),
            (r"Exception:", 0.9),
        ]

    def add_action(self, action_type: str, content: str, success: bool = True,
                   metadata: Dict[str, Any] = None) -> ActionRecord:
        """Add a new action to working memory"""

        # Calculate token count (rough estimation)
        token_count = len(content.split()) * 1.3

        # Calculate importance based on content patterns
        importance = self._calculate_importance(content, action_type, success)

        action = ActionRecord(
            timestamp=time.time(),
            action_type=action_type,
            content=content,
            success=success,
            token_count=int(token_count),
            importance=importance,
            metadata=metadata or {}
        )

        self.state.working_memory.append(action)
        self.total_actions += 1

        # Log high-importance or critical actions
        if importance > 0.8 or action_type in ['decision', 'error', 'goal_setting', 'pattern_alert']:
            status_emoji = "✅" if success else "❌"
            importance_emoji = "🔥" if importance > 0.8 else "📝"
            print(f"📝 Action logged: {status_emoji} {importance_emoji} [{action_type}] {content[:60]}...")

        # Trigger compression if needed
        if self._should_compress():
            self._compress_working_memory()

        return action

    def _calculate_importance(self, content: str, action_type: str, success: bool) -> float:
        """Calculate importance score for content"""
        base_importance = {
            'decision': 0.9,
            'reasoning': 0.7,
            'tool_call': 0.5,
            'observation': 0.4,
            'error': 0.8
        }.get(action_type, 0.5)

        # Adjust based on content patterns
        if not success:
            base_importance += 0.3  # Errors are more important

        # Pattern-based adjustments
        for pattern, adjustment in self.error_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                base_importance += adjustment
                break

        for pattern, reduction in self.tool_success_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                base_importance -= reduction
                break

        return min(1.0, max(0.1, base_importance))

    def _should_compress(self) -> bool:
        """Check if compression is needed"""
        current_tokens = sum(action.token_count for action in self.state.working_memory)
        token_ratio = current_tokens / self.max_context_tokens
        memory_ratio = len(self.state.working_memory) / self.max_working_memory

        should_compress = token_ratio > self.compression_threshold or memory_ratio > 0.8

        if should_compress:
            trigger_reason = []
            if token_ratio > self.compression_threshold:
                trigger_reason.append(f"token usage {token_ratio:.1%} > {self.compression_threshold:.1%}")
            if memory_ratio > 0.8:
                trigger_reason.append(f"memory usage {memory_ratio:.1%} > 80%")
            print(f"🔍 Compression triggered: {', '.join(trigger_reason)}")

        return should_compress

    def _compress_working_memory(self):
        """Compress working memory using smart strategies"""
        initial_count = len(self.state.working_memory)
        initial_tokens = sum(action.token_count for action in self.state.working_memory)

        print(f"🔄 Compressing context (current: {initial_count} actions, {initial_tokens} tokens)")

        # Separate by importance and age
        critical_actions = [a for a in self.state.working_memory if a.importance > 0.7]
        recent_actions = self.state.working_memory[-5:]  # Keep last 5 always
        compressible_actions = [a for a in self.state.working_memory
                              if a.importance <= 0.7 and a not in recent_actions]

        print(f"📋 Analysis: {len(critical_actions)} critical, {len(recent_actions)} recent, {len(compressible_actions)} compressible")

        # Keep critical + recent actions
        preserved_actions = []
        seen_actions = set()

        # Add critical actions (deduplicated)
        for action in critical_actions:
            action_hash = hashlib.md5(f"{action.content[:100]}".encode()).hexdigest()
            if action_hash not in seen_actions:
                preserved_actions.append(action)
                seen_actions.add(action_hash)

        # Add recent actions
        for action in recent_actions:
            if action not in preserved_actions:
                preserved_actions.append(action)

        # Update working memory and determine what's being dropped
        new_working_memory = preserved_actions[-self.max_working_memory:]
        dropped_actions = [a for a in self.state.working_memory if a not in new_working_memory]

        # Create compressed summary of dropped or compressible actions
        actions_to_summarise = compressible_actions if compressible_actions else dropped_actions
        if actions_to_summarise:
            summary = self._create_action_summary(actions_to_summarise)
            # Append to existing summary if present
            if self.state.short_term_summary:
                self.state.short_term_summary += f"\n{summary}"
            else:
                self.state.short_term_summary = summary
            print(f"📝 Created summary of {len(actions_to_summarise)} actions ({len(summary)} chars)")

        self.state.working_memory = new_working_memory
        self._compression_count += 1

        final_count = len(self.state.working_memory)
        final_tokens = sum(action.token_count for action in self.state.working_memory)
        actions_freed = initial_count - final_count
        tokens_freed = initial_tokens - final_tokens

        print(f"✅ Compression #{self._compression_count} complete: {final_count} actions ({actions_freed} freed), {final_tokens} tokens ({tokens_freed} freed)")

    def _create_action_summary(self, actions: List[ActionRecord]) -> str:
        """Create intelligent summary of actions"""
        if not actions:
            return ""

        # Group by action type
        grouped = {}
        for action in actions:
            action_type = action.action_type
            if action_type not in grouped:
                grouped[action_type] = []
            grouped[action_type].append(action)

        summary_parts = []

        # Summarise each type
        for action_type, type_actions in grouped.items():
            successful = sum(1 for a in type_actions if a.success)
            total = len(type_actions)

            if action_type == 'tool_call':
                summary_parts.append(f"Executed {total} tools ({successful} successful)")
            elif action_type == 'reasoning':
                summary_parts.append(f"Performed {total} reasoning steps")
            elif action_type == 'decision':
                decisions = [a.content[:50] for a in type_actions]
                summary_parts.append(f"Made {total} decisions: {'; '.join(decisions)}")

        return f"[COMPRESSED {len(actions)} actions]: " + "; ".join(summary_parts)

    def get_context_for_agent(self) -> str:
        """Generate optimised context for agent"""
        context_parts = []

        # Always include current goal if set
        if self.state.goal_state:
            context_parts.append(f"GOAL: {self.state.goal_state}")

        # Include compressed history if available
        if self.state.short_term_summary:
            context_parts.append(f"PREVIOUS ACTIONS: {self.state.short_term_summary}")

        # Include recent working memory
        if self.state.working_memory:
            recent_actions = []
            for action in self.state.working_memory[-5:]:  # Last 5 actions
                if action.compressed:
                    recent_actions.append(f"[{action.action_type}] {action.content[:100]}...")
                else:
                    recent_actions.append(f"[{action.action_type}] {action.content}")

            context_parts.append("RECENT ACTIONS:\n" + "\n".join(recent_actions))

        # Include decision trail
        if self.state.decision_trail:
            recent_decisions = self.state.decision_trail[-3:]  # Last 3 decisions
            decisions_text = "\n".join([f"- {d['decision']}: {d['rationale']}"
                                      for d in recent_decisions])
            context_parts.append(f"KEY DECISIONS:\n{decisions_text}")

        return "\n\n".join(context_parts)

    def log_decision(self, decision: str, rationale: str, impact: str = "medium"):
        """Log an important decision for future reference"""
        decision_record = {
            "timestamp": time.time(),
            "decision": decision,
            "rationale": rationale,
            "impact": impact,
            "phase": self.state.current_phase
        }

        self.state.decision_trail.append(decision_record)

        impact_emoji = {"high": "🔥", "medium": "📝", "low": "💭"}.get(impact, "📝")
        print(f"🤔 Decision logged ({impact} impact): '{decision[:60]}...'")
        print(f"   {impact_emoji} Rationale: {rationale[:100]}...")

        # Keep only recent decisions in memory
        if len(self.state.decision_trail) > 10:
            self.state.decision_trail = self.state.decision_trail[-10:]
            print(f"🗃️  Decision trail trimmed to last 10 entries")

    def set_goal(self, goal: str, subtasks: List[str] = None):
        """Set the current goal and track progress"""
        self.state.goal_state = {
            "main_goal": goal,
            "subtasks": subtasks or [],
            "completed_subtasks": [],
            "current_focus": goal,
            "start_time": time.time()
        }

        print(f"🎯 Goal set: '{goal}'")
        if subtasks:
            print(f"📋 Subtasks ({len(subtasks)}): {', '.join(subtasks)}")

        self.add_action(
            "goal_setting",
            f"Goal set: {goal} with {len(subtasks or [])} subtasks",
            success=True,
            metadata={"goal": goal, "subtask_count": len(subtasks or [])}
        )

    def mark_subtask_complete(self, subtask: str):
        """Mark a subtask as completed"""
        if "completed_subtasks" not in self.state.goal_state:
            self.state.goal_state["completed_subtasks"] = []

        self.state.goal_state["completed_subtasks"].append({
            "task": subtask,
            "completed_at": time.time()
        })

        completed = len(self.state.goal_state["completed_subtasks"])
        total = len(self.state.goal_state.get("subtasks", []))
        progress = f"{completed}/{total}" if total > 0 else str(completed)

        print(f"✅ Subtask completed: '{subtask}' (Progress: {progress})")

        self.add_action(
            "subtask_completion",
            f"Completed subtask: {subtask}",
            success=True,
            metadata={"subtask": subtask, "progress": progress}
        )

    def set_phase(self, phase: str):
        """Update current working phase"""
        old_phase = self.state.current_phase
        self.state.current_phase = phase

        print(f"🔄 Phase transition: {old_phase} → {phase}")

        self.add_action(
            "phase_change",
            f"Phase changed: {old_phase} → {phase}",
            success=True,
            metadata={"old_phase": old_phase, "new_phase": phase}
        )

    def track_error_pattern(self, error_msg: str):
        """Track recurring error patterns"""
        # Normalise error message
        normalised = re.sub(r'\d+', 'N', error_msg.lower())[:100]

        if normalised in self.state.error_patterns:
            self.state.error_patterns[normalised] += 1
            count = self.state.error_patterns[normalised]
            print(f"🔁 Error pattern recurring: '{error_msg[:50]}...' (occurrence #{count})")
        else:
            self.state.error_patterns[normalised] = 1
            print(f"🆕 New error pattern detected: '{error_msg[:50]}...'")

        # Alert if pattern is recurring (more than 2 occurrences)
        if self.state.error_patterns[normalised] > 2:
            print(f"⚠️  ALERT: Recurring error pattern #{self.state.error_patterns[normalised]} detected!")
            self.add_action(
                "pattern_alert",
                f"Recurring error pattern detected (#{self.state.error_patterns[normalised]}): {error_msg[:100]}",
                success=False,
                metadata={"pattern": normalised, "count": self.state.error_patterns[normalised]}
            )

    def get_statistics(self) -> Dict[str, Any]:
        """Get context management statistics"""
        current_tokens = sum(action.token_count for action in self.state.working_memory)

        return {
            "total_actions": self.total_actions,
            "working_memory_size": len(self.state.working_memory),
            "current_tokens": current_tokens,
            "token_utilisation": current_tokens / self.max_context_tokens,
            "current_phase": self.state.current_phase,
            "decisions_made": len(self.state.decision_trail),
            "error_patterns": len(self.state.error_patterns),
            "goal_progress": len(self.state.goal_state.get("completed_subtasks", [])),
            "compression_events": self._compression_count
        }

    def save_state(self, filepath: str):
        """Save context state to file"""
        state_data = asdict(self.state)
        state_data["manager_stats"] = self.get_statistics()

        with open(filepath, 'w') as f:
            json.dump(state_data, f, indent=2, default=str)

    def load_state(self, filepath: str):
        """Load context state from file"""
        with open(filepath, 'r') as f:
            data = json.load(f)

        # Reconstruct ActionRecord objects
        if "working_memory" in data:
            working_memory = []
            for action_data in data["working_memory"]:
                action = ActionRecord(**action_data)
                working_memory.append(action)
            data["working_memory"] = working_memory

        # Update state
        for key, value in data.items():
            if hasattr(self.state, key):
                setattr(self.state, key, value)