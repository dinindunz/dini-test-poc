"""
Context-Aware Agent Wrapper

Integrates context management with agent execution for long-running tasks.
"""

import time
import json
from typing import Any, Dict, List, Optional
from .context_manager import ContextManager, ActionRecord
from pathlib import Path


class ContextAwareAgent:
    """Agent wrapper with intelligent context management"""

    def __init__(self, base_agent, context_config: Dict[str, Any] = None):
        self.base_agent = base_agent
        self.context_manager = ContextManager(
            max_working_memory=context_config.get("max_working_memory", 10),
            max_context_tokens=context_config.get("max_context_tokens", 8000)
        )

        self.session_start = time.time()
        self.iteration_count = 0
        self.context_saves_dir = Path("context_saves")
        self.context_saves_dir.mkdir(exist_ok=True)

    def __call__(self, prompt: str, goal: str = None, subtasks: List[str] = None) -> Any:
        """Execute agent with context management"""
        self.iteration_count += 1

        # Set goal if provided
        if goal:
            self.context_manager.set_goal(goal, subtasks)

        # Log the incoming prompt
        self.context_manager.add_action(
            "user_prompt",
            prompt,
            success=True,
            metadata={"iteration": self.iteration_count}
        )

        try:
            # Create context-enhanced prompt
            enhanced_prompt = self._enhance_prompt_with_context(prompt)

            # Log reasoning about context enhancement
            self.context_manager.add_action(
                "reasoning",
                f"Enhanced prompt with context. Original: {len(prompt)} chars, Enhanced: {len(enhanced_prompt)} chars",
                success=True
            )

            # Execute base agent
            start_time = time.time()
            result = self.base_agent(enhanced_prompt)
            execution_time = time.time() - start_time

            # Log successful execution
            self.context_manager.add_action(
                "agent_execution",
                f"Agent executed successfully in {execution_time:.2f}s",
                success=True,
                metadata={
                    "execution_time": execution_time,
                    "iteration": self.iteration_count
                }
            )

            # Process and log the result
            self._process_agent_result(result)

            # Save context state periodically
            if self.iteration_count % 5 == 0:
                self._save_context_checkpoint()

            return result

        except Exception as e:
            # Log the error
            error_msg = str(e)
            self.context_manager.add_action(
                "error",
                f"Agent execution failed: {error_msg}",
                success=False,
                metadata={"exception_type": type(e).__name__}
            )

            # Track error patterns
            self.context_manager.track_error_pattern(error_msg)

            # Save error state
            self._save_error_context(error_msg)

            raise

    def _enhance_prompt_with_context(self, original_prompt: str) -> str:
        """Enhance prompt with relevant context"""
        context = self.context_manager.get_context_for_agent()

        if not context.strip():
            return original_prompt

        enhanced = f"""CONTEXT:
{context}

CURRENT REQUEST:
{original_prompt}

Please consider the context above when responding. Focus on the current request while being aware of previous actions and decisions."""

        return enhanced

    def _process_agent_result(self, result: Any):
        """Process and log agent result"""
        # Extract response text
        if hasattr(result, 'message'):
            response_text = result.message.get('content', [{}])[0].get('text', str(result.message))
        else:
            response_text = str(result)

        # Log the response
        self.context_manager.add_action(
            "agent_response",
            response_text[:500],  # Truncate for storage
            success=True,
            metadata={"full_length": len(response_text)}
        )

        # Extract and log any decisions made
        self._extract_decisions_from_response(response_text)

        # Extract and log any tool calls
        if hasattr(result, 'metrics'):
            metrics = result.metrics.get_summary()
            tool_calls = metrics.get('total_tool_calls', 0)
            if tool_calls > 0:
                self.context_manager.add_action(
                    "tool_usage",
                    f"Made {tool_calls} tool calls in this iteration",
                    success=True,
                    metadata=metrics
                )

    def _extract_decisions_from_response(self, response_text: str):
        """Extract key decisions from agent response"""
        # Look for decision patterns
        decision_patterns = [
            r"I will (.*?)(?:\.|$)",
            r"My approach is to (.*?)(?:\.|$)",
            r"I decided to (.*?)(?:\.|$)",
            r"The strategy is (.*?)(?:\.|$)"
        ]

        import re
        for pattern in decision_patterns:
            matches = re.findall(pattern, response_text, re.IGNORECASE)
            for match in matches:
                if len(match) > 10:  # Only log substantial decisions
                    self.context_manager.log_decision(
                        decision=match[:100],
                        rationale="Extracted from agent response",
                        impact="medium"
                    )
                    break  # Only log first substantial decision per response

    def set_phase(self, phase: str):
        """Update current working phase"""
        self.context_manager.set_phase(phase)

    def mark_subtask_complete(self, subtask: str):
        """Mark a subtask as completed"""
        self.context_manager.mark_subtask_complete(subtask)

    def get_context_stats(self) -> Dict[str, Any]:
        """Get context management statistics"""
        base_stats = self.context_manager.get_statistics()
        base_stats.update({
            "session_duration": time.time() - self.session_start,
            "iterations_completed": self.iteration_count,
            "context_saves": len(list(self.context_saves_dir.glob("*.json")))
        })
        return base_stats

    def _save_context_checkpoint(self):
        """Save context state as checkpoint"""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"context_checkpoint_{timestamp}.json"
        filepath = self.context_saves_dir / filename

        self.context_manager.save_state(str(filepath))

        # Also save enhanced statistics
        stats_file = self.context_saves_dir / f"stats_{timestamp}.json"
        with open(stats_file, 'w') as f:
            json.dump(self.get_context_stats(), f, indent=2)

        print(f"💾 Context checkpoint saved: {filename}")

    def _save_error_context(self, error_msg: str):
        """Save context when error occurs"""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"error_context_{timestamp}.json"
        filepath = self.context_saves_dir / filename

        error_data = {
            "error_message": error_msg,
            "iteration": self.iteration_count,
            "context_state": self.context_manager.get_context_for_agent(),
            "statistics": self.get_context_stats(),
            "timestamp": timestamp
        }

        with open(filepath, 'w') as f:
            json.dump(error_data, f, indent=2)

        print(f"💾 Error context saved: {filename}")

    def load_context_checkpoint(self, filepath: str):
        """Load context from checkpoint"""
        self.context_manager.load_state(filepath)
        print(f"📁 Context loaded from: {Path(filepath).name}")

    def get_context_summary(self) -> str:
        """Get human-readable context summary"""
        stats = self.get_context_stats()
        context = self.context_manager.get_context_for_agent()

        summary = f"""
📊 CONTEXT SUMMARY
{'=' * 40}
Session Duration: {stats['session_duration']:.1f}s
Iterations: {stats['iterations_completed']}
Total Actions: {stats['total_actions']}
Working Memory: {stats['working_memory_size']} actions
Token Utilisation: {stats['token_utilisation']:.1%}
Current Phase: {stats['current_phase']}
Decisions Made: {stats['decisions_made']}
Error Patterns: {stats['error_patterns']}

CURRENT CONTEXT:
{context}
"""
        return summary

    def reset_context(self):
        """Reset context manager to fresh state"""
        self.context_manager = ContextManager()
        self.iteration_count = 0
        self.session_start = time.time()
        print("🔄 Context reset to fresh state")


# Usage examples and testing functions
def create_context_aware_agent(base_agent, config: Dict[str, Any] = None):
    """Factory function to create context-aware agent"""
    default_config = {
        "max_working_memory": 12,
        "max_context_tokens": 8000
    }

    if config:
        default_config.update(config)

    return ContextAwareAgent(base_agent, default_config)


def demo_context_management(agent):
    """Demonstrate context management features"""
    print("🧪 Testing Context Management System")
    print("=" * 50)

    # Set a goal
    agent.context_manager.set_goal(
        "Implement a new feature",
        ["analyse requirements", "design solution", "implement code", "test"]
    )

    # Simulate multiple agent iterations
    responses = [
        "I'll start by analysing the requirements for this feature.",
        "Based on the analysis, I need to design a solution architecture.",
        "Now implementing the core functionality with proper error handling.",
        "Testing the implementation to ensure it works correctly.",
        "The feature is complete and tested successfully."
    ]

    for i, response in enumerate(responses):
        print(f"\n--- Iteration {i+1} ---")

        # Simulate user prompt
        user_prompt = f"Continue with step {i+1} of the implementation"

        # Add some context actions
        agent.context_manager.add_action(
            "reasoning",
            f"Step {i+1}: {response}",
            success=True
        )

        if i == 2:  # Simulate an error in step 3
            agent.context_manager.track_error_pattern("File not found: config.py")

        if i > 0:
            agent.context_manager.mark_subtask_complete(agent.context_manager.state.goal_state["subtasks"][i-1])

        # Show context evolution
        context = agent.context_manager.get_context_for_agent()
        print(f"Context size: {len(context)} chars")

        stats = agent.get_context_stats()
        print(f"Memory: {stats['working_memory_size']}/{stats['token_utilisation']:.1%} capacity")

    print("\n" + agent.get_context_summary())


if __name__ == "__main__":
    # Demo with mock agent
    class MockAgent:
        def __call__(self, prompt):
            return type('Result', (), {
                'message': {'content': [{'text': f"Mock response to: {prompt[:50]}..."}]},
                'metrics': type('Metrics', (), {'get_summary': lambda: {'total_tool_calls': 1}})()
            })()

    mock_agent = MockAgent()
    context_agent = create_context_aware_agent(mock_agent)
    demo_context_management(context_agent)