"""
DOER Platform - Agents Package

Provides autonomous agents for case automation:
- State machine for case lifecycle
- Timeline generator
- Task automation
- Document drafting
- Negotiation bot
"""

from app.agents.state_machine import (
    CaseState,
    CaseStateMachine,
    StateContext,
    StateTransition,
    VALID_TRANSITIONS,
    get_state_machine,
    create_state_machine
)
