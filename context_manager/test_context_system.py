#!/usr/bin/env python3
"""
Test Context Management System

Verify that context management works correctly for agentic loops.
"""

import time
from context_manager.context_manager import ContextManager
from context_manager.context_aware_agent import create_context_aware_agent


class MockAgent:
    """Mock agent for testing context management"""

    def __init__(self):
        self.call_count = 0

    def __call__(self, prompt):
        self.call_count += 1

        # Simulate different types of responses
        responses = [
            "I'll start by analysing the repository structure.",
            "Found the main configuration files. Now implementing the feature.",
            "Encountered an error with the database connection. Fixing it.",
            "Successfully implemented the core functionality.",
            "Running tests to verify the implementation works correctly.",
            "All tests pass. The feature is ready for review."
        ]

        response_text = responses[min(self.call_count - 1, len(responses) - 1)]

        # Capture call_count for use in lambda
        call_count = self.call_count

        # Simulate agent result structure
        return type('Result', (), {
            'message': {'content': [{'text': response_text}]},
            'metrics': type('Metrics', (), {
                'get_summary': lambda self: {
                    'total_tool_calls': 2,
                    'execution_time': 1.5,
                    'tokens_used': 150 + (call_count * 20)
                }
            })()
        })()


def test_basic_context_management():
    """Test basic context manager functionality"""
    print("🧪 Testing Basic Context Management")
    print("-" * 40)

    manager = ContextManager(max_working_memory=5, max_context_tokens=1000)

    # Test adding actions
    manager.add_action("user_prompt", "Please implement a login system", True)
    manager.add_action("reasoning", "I need to analyse the current authentication setup", True)
    manager.add_action("tool_call", "git status", True, {"command": "git"})
    manager.add_action("error", "File not found: config.py", False)
    manager.add_action("decision", "I'll create the missing config file", True)

    assert len(manager.state.working_memory) == 5, "Should have 5 actions"

    # Test importance calculation
    high_importance_actions = [a for a in manager.state.working_memory if a.importance > 0.7]
    assert len(high_importance_actions) >= 2, "Should have high importance actions"

    # Test context generation
    context = manager.get_context_for_agent()
    assert len(context) > 0, "Should generate context"
    assert "RECENT ACTIONS" in context, "Should include recent actions"

    print("✅ Basic context management working")


def test_context_compression():
    """Test context compression when memory is full"""
    print("\n🧪 Testing Context Compression")
    print("-" * 40)

    manager = ContextManager(max_working_memory=3, max_context_tokens=500)

    # Add many actions to trigger compression
    for i in range(8):
        manager.add_action(
            "tool_call",
            f"Running command {i}: ls -la directory_{i}",
            True,
            {"iteration": i}
        )

    # Should have compressed to max working memory
    assert len(manager.state.working_memory) <= 3, "Should compress working memory"
    assert len(manager.state.short_term_summary) > 0, "Should create summary"

    print("✅ Context compression working")


def test_context_aware_agent():
    """Test the full context-aware agent"""
    print("\n🧪 Testing Context-Aware Agent")
    print("-" * 40)

    mock_agent = MockAgent()
    context_agent = create_context_aware_agent(mock_agent, {
        "max_working_memory": 8,
        "max_context_tokens": 2000
    })

    # Set a goal
    context_agent.context_manager.set_goal(
        "Implement user authentication",
        ["analyse current setup", "design solution", "implement code", "test"]
    )

    # Simulate multiple iterations
    prompts = [
        "Start implementing user authentication",
        "Continue with the authentication setup",
        "Handle any errors that occurred",
        "Finalise the authentication implementation",
        "Test the authentication system"
    ]

    for i, prompt in enumerate(prompts):
        print(f"\n--- Iteration {i+1} ---")

        # Set phase
        phases = ["analysis", "implementation", "debugging", "finalisation", "testing"]
        context_agent.set_phase(phases[i])

        # Execute
        result = context_agent(prompt)

        # Mark subtask complete
        if i < len(context_agent.context_manager.state.goal_state.get("subtasks", [])):
            subtask = context_agent.context_manager.state.goal_state["subtasks"][i]
            context_agent.mark_subtask_complete(subtask)

        # Check result
        assert hasattr(result, 'message'), "Should return proper result"

        # Check context stats
        stats = context_agent.get_context_stats()
        print(f"Actions: {stats['total_actions']}, Memory: {stats['working_memory_size']}")

    # Final verification
    final_stats = context_agent.get_context_stats()
    assert final_stats['total_actions'] > 10, "Should have recorded multiple actions"
    assert final_stats['iterations_completed'] == 5, "Should have completed 5 iterations"

    print("✅ Context-aware agent working")


def test_decision_tracking():
    """Test decision tracking and retrieval"""
    print("\n🧪 Testing Decision Tracking")
    print("-" * 40)

    manager = ContextManager()

    # Log some decisions
    manager.log_decision(
        "Use JWT tokens for authentication",
        "They provide stateless authentication and are widely supported",
        "high"
    )

    manager.log_decision(
        "Store tokens in httpOnly cookies",
        "More secure than localStorage for XSS protection",
        "medium"
    )

    assert len(manager.state.decision_trail) == 2, "Should track decisions"

    context = manager.get_context_for_agent()
    assert "KEY DECISIONS" in context, "Should include decisions in context"
    assert "JWT tokens" in context, "Should include decision content"

    print("✅ Decision tracking working")


def test_error_pattern_recognition():
    """Test error pattern recognition"""
    print("\n🧪 Testing Error Pattern Recognition")
    print("-" * 40)

    manager = ContextManager()

    # Simulate recurring errors
    manager.track_error_pattern("File not found: config.py")
    manager.track_error_pattern("File not found: settings.py")
    manager.track_error_pattern("File not found: config.py")  # Repeat
    manager.track_error_pattern("File not found: config.py")  # Repeat again

    # Should detect the pattern
    assert len(manager.state.error_patterns) > 0, "Should track error patterns"

    # Should create pattern alert
    pattern_alerts = [a for a in manager.state.working_memory
                     if a.action_type == "pattern_alert"]
    assert len(pattern_alerts) > 0, "Should create pattern alert"

    print("✅ Error pattern recognition working")


def run_all_tests():
    """Run all context management tests"""
    print("🚀 Running Context Management Test Suite")
    print("=" * 50)

    try:
        test_basic_context_management()
        test_context_compression()
        test_decision_tracking()
        test_error_pattern_recognition()
        test_context_aware_agent()

        print("\n🎉 All Tests Passed!")
        print("=" * 50)
        print("Context management system is working correctly.")

    except AssertionError as e:
        print(f"\n❌ Test Failed: {e}")
        return False
    except Exception as e:
        print(f"\n💥 Test Error: {e}")
        return False

    return True


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)