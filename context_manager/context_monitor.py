#!/usr/bin/env python3
"""
Context Monitor Utility

Monitor and manage context state for long-running agent sessions.

Usage:
    python context_monitor.py status           # Show current context status
    python context_monitor.py history          # Show action history
    python context_monitor.py stats           # Show detailed statistics
    python context_monitor.py reset           # Reset context (with confirmation)
    python context_monitor.py export [file]   # Export context to file
"""

import sys
import json
import time
from pathlib import Path
from .context_manager import ContextManager


def show_status():
    """Show current context status"""
    print("🧠 Context Manager Status")
    print("=" * 40)

    # Check for context saves
    context_dir = Path("context_saves")
    if not context_dir.exists():
        print("❌ No context saves directory found")
        return

    # Find latest context file
    context_files = list(context_dir.glob("context_checkpoint_*.json"))
    if not context_files:
        print("📭 No context checkpoints found")
        return

    latest_file = max(context_files, key=lambda f: f.stat().st_mtime)

    # Load and display
    manager = ContextManager()
    manager.load_state(str(latest_file))

    stats = manager.get_statistics()

    print(f"📁 Latest checkpoint: {latest_file.name}")
    print(f"📊 Working memory: {stats['working_memory_size']} actions")
    print(f"🎯 Current phase: {stats['current_phase']}")
    print(f"📈 Total actions: {stats['total_actions']}")
    print(f"💾 Token usage: {stats['token_utilisation']:.1%}")
    print(f"🔄 Decisions made: {stats['decisions_made']}")
    print(f"⚠️  Error patterns: {stats['error_patterns']}")

    if manager.state.goal_state:
        goal = manager.state.goal_state
        completed = len(goal.get("completed_subtasks", []))
        total = len(goal.get("subtasks", []))
        print(f"🎯 Goal progress: {completed}/{total} subtasks")
        print(f"📝 Main goal: {goal.get('main_goal', 'Not set')}")


def show_history():
    """Show recent action history"""
    print("📜 Recent Action History")
    print("=" * 40)

    context_dir = Path("context_saves")
    if not context_dir.exists():
        print("❌ No context saves directory found")
        return

    context_files = list(context_dir.glob("context_checkpoint_*.json"))
    if not context_files:
        print("📭 No context checkpoints found")
        return

    latest_file = max(context_files, key=lambda f: f.stat().st_mtime)

    manager = ContextManager()
    manager.load_state(str(latest_file))

    print(f"Last 10 actions from {latest_file.name}:")
    print("-" * 60)

    for i, action in enumerate(manager.state.working_memory[-10:], 1):
        timestamp = time.strftime("%H:%M:%S", time.localtime(action.timestamp))
        status = "✅" if action.success else "❌"
        importance = "🔥" if action.importance > 0.7 else "📝"

        print(f"{i:2d}. [{timestamp}] {status} {importance} [{action.action_type}]")
        print(f"    {action.content[:80]}...")
        if action.metadata:
            key_metadata = {k: v for k, v in action.metadata.items() if k in ['iteration', 'execution_time']}
            if key_metadata:
                print(f"    Metadata: {key_metadata}")
        print()


def show_detailed_stats():
    """Show detailed statistics"""
    print("📊 Detailed Context Statistics")
    print("=" * 40)

    context_dir = Path("context_saves")
    if not context_dir.exists():
        print("❌ No context saves directory found")
        return

    # Load latest context
    context_files = list(context_dir.glob("context_checkpoint_*.json"))
    if not context_files:
        print("📭 No context checkpoints found")
        return

    latest_file = max(context_files, key=lambda f: f.stat().st_mtime)

    manager = ContextManager()
    manager.load_state(str(latest_file))

    # Action type breakdown
    action_types = {}
    importance_levels = {"high": 0, "medium": 0, "low": 0}
    success_rate = {"success": 0, "failure": 0}

    for action in manager.state.working_memory:
        # Count by type
        action_types[action.action_type] = action_types.get(action.action_type, 0) + 1

        # Count by importance
        if action.importance > 0.7:
            importance_levels["high"] += 1
        elif action.importance > 0.4:
            importance_levels["medium"] += 1
        else:
            importance_levels["low"] += 1

        # Count success/failure
        if action.success:
            success_rate["success"] += 1
        else:
            success_rate["failure"] += 1

    print("Action Types:")
    for action_type, count in sorted(action_types.items()):
        print(f"  {action_type}: {count}")

    print(f"\nImportance Distribution:")
    total_actions = sum(importance_levels.values())
    for level, count in importance_levels.items():
        percentage = (count / total_actions * 100) if total_actions > 0 else 0
        print(f"  {level}: {count} ({percentage:.1f}%)")

    print(f"\nSuccess Rate:")
    total_attempts = sum(success_rate.values())
    success_pct = (success_rate["success"] / total_attempts * 100) if total_attempts > 0 else 0
    print(f"  Success: {success_rate['success']} ({success_pct:.1f}%)")
    print(f"  Failure: {success_rate['failure']} ({100-success_pct:.1f}%)")

    # Error patterns
    if manager.state.error_patterns:
        print(f"\nTop Error Patterns:")
        sorted_errors = sorted(manager.state.error_patterns.items(), key=lambda x: x[1], reverse=True)
        for pattern, count in sorted_errors[:5]:
            print(f"  {count}x: {pattern[:50]}...")

    # Decision trail
    if manager.state.decision_trail:
        print(f"\nRecent Decisions:")
        for decision in manager.state.decision_trail[-3:]:
            print(f"  • {decision['decision']}")
            print(f"    Rationale: {decision['rationale']}")


def reset_context():
    """Reset context with confirmation"""
    print("⚠️  Context Reset")
    print("=" * 40)

    response = input("Are you sure you want to reset all context? This cannot be undone. (yes/no): ")

    if response.lower() != "yes":
        print("❌ Reset cancelled")
        return

    context_dir = Path("context_saves")
    if context_dir.exists():
        # Archive existing context
        import shutil
        archive_dir = Path(f"context_archive_{int(time.time())}")
        shutil.move(str(context_dir), str(archive_dir))
        print(f"📦 Existing context archived to: {archive_dir}")

    context_dir.mkdir()
    print("✅ Context reset successfully")


def export_context(output_file: str = None):
    """Export context to file"""
    if not output_file:
        output_file = f"context_export_{int(time.time())}.json"

    print(f"📤 Exporting context to: {output_file}")

    context_dir = Path("context_saves")
    if not context_dir.exists():
        print("❌ No context saves directory found")
        return

    context_files = list(context_dir.glob("context_checkpoint_*.json"))
    if not context_files:
        print("📭 No context checkpoints found")
        return

    latest_file = max(context_files, key=lambda f: f.stat().st_mtime)

    manager = ContextManager()
    manager.load_state(str(latest_file))

    # Create comprehensive export
    export_data = {
        "export_timestamp": time.time(),
        "source_checkpoint": latest_file.name,
        "statistics": manager.get_statistics(),
        "context_state": manager.get_context_for_agent(),
        "full_state": {
            "working_memory": [
                {
                    "timestamp": action.timestamp,
                    "action_type": action.action_type,
                    "content": action.content,
                    "success": action.success,
                    "importance": action.importance,
                    "metadata": action.metadata
                }
                for action in manager.state.working_memory
            ],
            "decision_trail": manager.state.decision_trail,
            "error_patterns": manager.state.error_patterns,
            "goal_state": manager.state.goal_state
        }
    }

    with open(output_file, 'w') as f:
        json.dump(export_data, f, indent=2, default=str)

    print(f"✅ Context exported successfully")
    print(f"📊 Exported {len(manager.state.working_memory)} actions")


def main():
    if len(sys.argv) < 2:
        print("Context Monitor Utility")
        print("=" * 30)
        print("Usage:")
        print("  python context_monitor.py status")
        print("  python context_monitor.py history")
        print("  python context_monitor.py stats")
        print("  python context_monitor.py reset")
        print("  python context_monitor.py export [filename]")
        sys.exit(1)

    command = sys.argv[1].lower()

    try:
        if command == "status":
            show_status()
        elif command == "history":
            show_history()
        elif command == "stats":
            show_detailed_stats()
        elif command == "reset":
            reset_context()
        elif command == "export":
            output_file = sys.argv[2] if len(sys.argv) > 2 else None
            export_context(output_file)
        else:
            print(f"❌ Unknown command: {command}")
            print("Available commands: status, history, stats, reset, export")
            sys.exit(1)

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Handle running from different directories
    import sys
    from pathlib import Path

    # Add parent directory to path so we can import the package
    parent_dir = Path(__file__).parent.parent
    if str(parent_dir) not in sys.path:
        sys.path.insert(0, str(parent_dir))

    main()