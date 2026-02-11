"""
DOER Platform - Case State Machine

Manages case lifecycle through defined states with entry/exit actions.

STATES:
- INTAKE: Initial submission, document collection
- VERIFICATION: Document verification, land record check
- ANALYSIS: Dispute analysis, timeline generation
- NEGOTIATION: Settlement negotiation, mediation
- RESOLUTION: Agreement reached, documentation
- CLOSURE: Case closed, final archival

PRODUCTION UPGRADES:
- Persist state history to database
- Add audit logging for transitions
- Implement rollback capability
- Add webhook notifications for state changes
"""

from enum import Enum
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass, field
from datetime import datetime
import asyncio


class CaseState(str, Enum):
    """Case lifecycle states."""
    INTAKE = "intake"
    VERIFICATION = "verification"
    ANALYSIS = "analysis"
    NEGOTIATION = "negotiation"
    RESOLUTION = "resolution"
    CLOSURE = "closure"


# Valid state transitions
VALID_TRANSITIONS: Dict[CaseState, List[CaseState]] = {
    CaseState.INTAKE: [CaseState.VERIFICATION],
    CaseState.VERIFICATION: [CaseState.ANALYSIS, CaseState.INTAKE],  # Can go back for more docs
    CaseState.ANALYSIS: [CaseState.NEGOTIATION, CaseState.VERIFICATION],
    CaseState.NEGOTIATION: [CaseState.RESOLUTION, CaseState.ANALYSIS],  # Back if no agreement
    CaseState.RESOLUTION: [CaseState.CLOSURE, CaseState.NEGOTIATION],
    CaseState.CLOSURE: []  # Terminal state
}


@dataclass
class StateTransition:
    """Records a state transition."""
    from_state: CaseState
    to_state: CaseState
    timestamp: datetime
    reason: Optional[str] = None
    triggered_by: Optional[str] = None  # user, system, agent
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StateContext:
    """Context passed to state handlers."""
    case_id: int
    current_state: CaseState
    previous_state: Optional[CaseState] = None
    transition_history: List[StateTransition] = field(default_factory=list)
    data: Dict[str, Any] = field(default_factory=dict)


class CaseStateMachine:
    """
    State machine for managing case lifecycle.
    
    Supports:
    - Entry/exit actions for each state
    - Transition validation
    - Event triggers
    - Async action execution
    """
    
    def __init__(self, case_id: int, initial_state: CaseState = CaseState.INTAKE):
        """
        Initialize the state machine.
        
        Args:
            case_id: Case ID being managed
            initial_state: Starting state
        """
        self.case_id = case_id
        self.current_state = initial_state
        self.context = StateContext(
            case_id=case_id,
            current_state=initial_state
        )
        
        # Registered handlers
        self._entry_handlers: Dict[CaseState, List[Callable]] = {state: [] for state in CaseState}
        self._exit_handlers: Dict[CaseState, List[Callable]] = {state: [] for state in CaseState}
        self._transition_handlers: List[Callable] = []
        
        # Register default handlers
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """Register default entry/exit handlers for each state."""
        
        # INTAKE handlers
        self.on_enter(CaseState.INTAKE, self._on_enter_intake)
        self.on_exit(CaseState.INTAKE, self._on_exit_intake)
        
        # VERIFICATION handlers
        self.on_enter(CaseState.VERIFICATION, self._on_enter_verification)
        
        # ANALYSIS handlers
        self.on_enter(CaseState.ANALYSIS, self._on_enter_analysis)
        
        # NEGOTIATION handlers
        self.on_enter(CaseState.NEGOTIATION, self._on_enter_negotiation)
        
        # RESOLUTION handlers
        self.on_enter(CaseState.RESOLUTION, self._on_enter_resolution)
        
        # CLOSURE handlers
        self.on_enter(CaseState.CLOSURE, self._on_enter_closure)
    
    def on_enter(self, state: CaseState, handler: Callable):
        """Register handler for state entry."""
        self._entry_handlers[state].append(handler)
    
    def on_exit(self, state: CaseState, handler: Callable):
        """Register handler for state exit."""
        self._exit_handlers[state].append(handler)
    
    def on_transition(self, handler: Callable):
        """Register handler for any state transition."""
        self._transition_handlers.append(handler)
    
    def can_transition(self, to_state: CaseState) -> bool:
        """Check if transition to target state is valid."""
        return to_state in VALID_TRANSITIONS.get(self.current_state, [])
    
    async def transition(
        self,
        to_state: CaseState,
        reason: Optional[str] = None,
        triggered_by: str = "system"
    ) -> bool:
        """
        Transition to a new state.
        
        Args:
            to_state: Target state
            reason: Reason for transition
            triggered_by: Who triggered (user, system, agent)
            
        Returns:
            True if transition successful
        """
        if not self.can_transition(to_state):
            print(f"Invalid transition: {self.current_state} -> {to_state}")
            return False
        
        from_state = self.current_state
        
        # Record transition
        transition = StateTransition(
            from_state=from_state,
            to_state=to_state,
            timestamp=datetime.utcnow(),
            reason=reason,
            triggered_by=triggered_by
        )
        self.context.transition_history.append(transition)
        
        # Execute exit handlers
        for handler in self._exit_handlers[from_state]:
            await self._execute_handler(handler)
        
        # Update state
        self.context.previous_state = from_state
        self.current_state = to_state
        self.context.current_state = to_state
        
        # Execute transition handlers
        for handler in self._transition_handlers:
            await self._execute_handler(handler, transition)
        
        # Execute entry handlers
        for handler in self._entry_handlers[to_state]:
            await self._execute_handler(handler)
        
        print(f"Case {self.case_id}: {from_state.value} -> {to_state.value}")
        return True
    
    async def _execute_handler(self, handler: Callable, *args):
        """Execute a handler (sync or async)."""
        try:
            if asyncio.iscoroutinefunction(handler):
                await handler(self.context, *args)
            else:
                handler(self.context, *args)
        except Exception as e:
            print(f"Handler error: {e}")
    
    # Default handlers
    async def _on_enter_intake(self, context: StateContext):
        """Entry action for INTAKE state."""
        print(f"[INTAKE] Case {context.case_id}: Starting intake process")
        context.data["intake_started_at"] = datetime.utcnow().isoformat()
    
    async def _on_exit_intake(self, context: StateContext):
        """Exit action for INTAKE state."""
        print(f"[INTAKE] Case {context.case_id}: Intake completed")
        context.data["intake_completed_at"] = datetime.utcnow().isoformat()
    
    async def _on_enter_verification(self, context: StateContext):
        """Entry action for VERIFICATION state."""
        print(f"[VERIFICATION] Case {context.case_id}: Starting document verification")
        # Trigger verification agent
        context.data["verification_started_at"] = datetime.utcnow().isoformat()
    
    async def _on_enter_analysis(self, context: StateContext):
        """Entry action for ANALYSIS state."""
        print(f"[ANALYSIS] Case {context.case_id}: Starting dispute analysis")
        # Trigger timeline generation
        context.data["analysis_started_at"] = datetime.utcnow().isoformat()
    
    async def _on_enter_negotiation(self, context: StateContext):
        """Entry action for NEGOTIATION state."""
        print(f"[NEGOTIATION] Case {context.case_id}: Starting negotiation phase")
        # Trigger negotiation bot
        context.data["negotiation_started_at"] = datetime.utcnow().isoformat()
    
    async def _on_enter_resolution(self, context: StateContext):
        """Entry action for RESOLUTION state."""
        print(f"[RESOLUTION] Case {context.case_id}: Generating resolution documents")
        # Trigger document drafting agent
        context.data["resolution_started_at"] = datetime.utcnow().isoformat()
    
    async def _on_enter_closure(self, context: StateContext):
        """Entry action for CLOSURE state."""
        print(f"[CLOSURE] Case {context.case_id}: Case closed")
        context.data["closed_at"] = datetime.utcnow().isoformat()
    
    def get_state_info(self) -> Dict[str, Any]:
        """Get current state information."""
        return {
            "case_id": self.case_id,
            "current_state": self.current_state.value,
            "previous_state": self.context.previous_state.value if self.context.previous_state else None,
            "valid_transitions": [s.value for s in VALID_TRANSITIONS.get(self.current_state, [])],
            "transition_count": len(self.context.transition_history),
            "context_data": self.context.data
        }


# State machine registry
_machines: Dict[int, CaseStateMachine] = {}


def get_state_machine(case_id: int) -> CaseStateMachine:
    """Get or create a state machine for a case."""
    if case_id not in _machines:
        _machines[case_id] = CaseStateMachine(case_id)
    return _machines[case_id]


def create_state_machine(case_id: int, initial_state: CaseState = CaseState.INTAKE) -> CaseStateMachine:
    """Create a new state machine for a case."""
    machine = CaseStateMachine(case_id, initial_state)
    _machines[case_id] = machine
    return machine
