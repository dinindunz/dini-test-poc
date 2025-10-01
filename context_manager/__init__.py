"""
Context Manager Package

Intelligent context window management for long-running agent tasks.
Like redwood tree rings: recent visible, old compressed into core.
"""

from .context_manager import ContextManager, ActionRecord, ContextState
from .redwood_agent import RedwoodAgent, create_redwood_agent

__all__ = [
    'ContextManager',
    'ActionRecord',
    'ContextState',
    'RedwoodAgent',
    'create_redwood_agent'
]