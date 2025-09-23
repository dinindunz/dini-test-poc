"""
Context Manager Package

Intelligent context window management for long-running agent tasks.
"""

from .context_manager import ContextManager, ActionRecord, ContextState
from .context_aware_agent import ContextAwareAgent, create_context_aware_agent

__all__ = [
    'ContextManager',
    'ActionRecord',
    'ContextState',
    'ContextAwareAgent',
    'create_context_aware_agent'
]