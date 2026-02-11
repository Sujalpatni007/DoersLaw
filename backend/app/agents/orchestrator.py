"""
DOER Platform - Agent Orchestrator

Central orchestrator that coordinates all agents for a case.

FEATURES:
- Coordinates state transitions
- Triggers appropriate agents per state
- Tracks agent runs
- Provides unified API

PRODUCTION UPGRADES:
- Event-driven architecture
- Distributed tracing
- Agent health monitoring
- Retry policies
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional
from enum import Enum
import asyncio

from app.agents.state_machine import (
    CaseState, 
    CaseStateMachine, 
    get_state_machine, 
    create_state_machine
)
from app.agents.timeline_agent import get_timeline_agent
from app.agents.task_agent import get_task_agent, TriggerType, TaskPriority
from app.agents.document_agent import get_document_agent
from app.agents.negotiation_agent import get_negotiation_agent, Claim


class AgentRunStatus(str, Enum):
    """Status of an agent run."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class AgentRun:
    """Tracks an agent orchestration run."""
    run_id: str
    case_id: int
    triggered_by: str
    started_at: datetime
    current_state: CaseState
    status: AgentRunStatus = AgentRunStatus.PENDING
    completed_at: Optional[datetime] = None
    results: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "case_id": self.case_id,
            "triggered_by": self.triggered_by,
            "started_at": self.started_at.isoformat(),
            "current_state": self.current_state.value,
            "status": self.status.value,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "results": self.results,
            "errors": self.errors
        }


class AgentOrchestrator:
    """
    Orchestrates all agents for case automation.
    """
    
    def __init__(self):
        """Initialize the orchestrator."""
        self.runs: Dict[str, AgentRun] = {}
        self.run_counter = 0
        
        # Get agent instances
        self.timeline_agent = get_timeline_agent()
        self.task_agent = get_task_agent()
        self.document_agent = get_document_agent()
        self.negotiation_agent = get_negotiation_agent()
    
    def _generate_run_id(self, case_id: int) -> str:
        """Generate unique run ID."""
        self.run_counter += 1
        return f"RUN-{case_id}-{self.run_counter:04d}"
    
    async def run_case_automation(
        self,
        case_id: int,
        dispute_type: str = "ownership_dispute",
        complexity: str = "medium",
        location: str = "delhi",
        area_acres: float = 1.0,
        triggered_by: str = "system"
    ) -> AgentRun:
        """
        Run full agent automation for a case.
        
        This orchestrates all agents based on the case state.
        
        Args:
            case_id: Case ID to process
            dispute_type: Type of dispute
            complexity: Complexity level
            location: Location for valuation
            area_acres: Land area
            triggered_by: Who triggered the run
            
        Returns:
            AgentRun with results
        """
        # Create agent run
        state_machine = get_state_machine(case_id)
        run = AgentRun(
            run_id=self._generate_run_id(case_id),
            case_id=case_id,
            triggered_by=triggered_by,
            started_at=datetime.utcnow(),
            current_state=state_machine.current_state,
            status=AgentRunStatus.RUNNING
        )
        self.runs[run.run_id] = run
        
        print(f"\n🤖 Starting Agent Orchestration: {run.run_id}")
        print(f"   Case: {case_id} | State: {state_machine.current_state.value}")
        
        try:
            # Execute agents based on current state
            if state_machine.current_state == CaseState.INTAKE:
                await self._handle_intake(run, case_id, dispute_type, complexity, location, area_acres)
            
            elif state_machine.current_state == CaseState.VERIFICATION:
                await self._handle_verification(run, case_id)
            
            elif state_machine.current_state == CaseState.ANALYSIS:
                await self._handle_analysis(run, case_id, dispute_type, complexity, location, area_acres)
            
            elif state_machine.current_state == CaseState.NEGOTIATION:
                await self._handle_negotiation(run, case_id, dispute_type, location, area_acres)
            
            elif state_machine.current_state == CaseState.RESOLUTION:
                await self._handle_resolution(run, case_id)
            
            elif state_machine.current_state == CaseState.CLOSURE:
                await self._handle_closure(run, case_id)
            
            run.status = AgentRunStatus.COMPLETED
            run.completed_at = datetime.utcnow()
            
            print(f"✅ Agent Run Completed: {run.run_id}")
            
        except Exception as e:
            run.status = AgentRunStatus.FAILED
            run.errors.append(str(e))
            run.completed_at = datetime.utcnow()
            print(f"❌ Agent Run Failed: {e}")
        
        return run
    
    async def _handle_intake(
        self,
        run: AgentRun,
        case_id: int,
        dispute_type: str,
        complexity: str,
        location: str,
        area_acres: float
    ):
        """Handle INTAKE state automation."""
        print("   📥 Processing INTAKE...")
        
        # Generate timeline
        timeline = self.timeline_agent.generate_timeline(
            case_id=case_id,
            dispute_type=dispute_type,
            complexity=complexity,
            location_type="urban" if location in ["delhi", "mumbai", "bangalore"] else "rural"
        )
        run.results["timeline"] = timeline
        print(f"      ✓ Timeline generated: {timeline['total_days']} days, {timeline['milestone_count']} milestones")
        
        # Create intake tasks
        tasks = await self.task_agent.create_tasks_for_state(case_id, "intake")
        run.results["tasks_created"] = len(tasks)
        print(f"      ✓ Created {len(tasks)} intake tasks")
    
    async def _handle_verification(self, run: AgentRun, case_id: int):
        """Handle VERIFICATION state automation."""
        print("   🔍 Processing VERIFICATION...")
        
        # Create verification tasks
        tasks = await self.task_agent.create_tasks_for_state(case_id, "verification")
        run.results["tasks_created"] = len(tasks)
        print(f"      ✓ Created {len(tasks)} verification tasks")
        
        # Note: Actual OCR/verification would be triggered here
        run.results["verification_note"] = "Document verification ready for processing"
    
    async def _handle_analysis(
        self,
        run: AgentRun,
        case_id: int,
        dispute_type: str,
        complexity: str,
        location: str,
        area_acres: float
    ):
        """Handle ANALYSIS state automation."""
        print("   📊 Processing ANALYSIS...")
        
        # Get land valuation
        valuation = self.negotiation_agent.estimate_land_value(
            area_acres=area_acres,
            location=location,
            land_type="agricultural"
        )
        run.results["land_valuation"] = valuation
        print(f"      ✓ Land valued at ₹{valuation['total_value_lakhs']} lakhs")
        
        # Create analysis tasks
        tasks = await self.task_agent.create_tasks_for_state(case_id, "analysis")
        run.results["tasks_created"] = len(tasks)
        print(f"      ✓ Created {len(tasks)} analysis tasks")
    
    async def _handle_negotiation(
        self,
        run: AgentRun,
        case_id: int,
        dispute_type: str,
        location: str,
        area_acres: float
    ):
        """Handle NEGOTIATION state automation."""
        print("   🤝 Processing NEGOTIATION...")
        
        # Mock claims for demo
        party_1 = Claim(
            party_name="Party A",
            claimed_percentage=60,
            years_of_possession=15,
            supporting_documents=5
        )
        party_2 = Claim(
            party_name="Party B",
            claimed_percentage=40,
            years_of_possession=8,
            supporting_documents=3
        )
        
        # Get land value
        valuation = self.negotiation_agent.estimate_land_value(
            area_acres=area_acres,
            location=location
        )
        
        # Generate settlement proposals
        proposals = self.negotiation_agent.generate_proposals(
            case_id=case_id,
            dispute_type=dispute_type,
            party_1=party_1,
            party_2=party_2,
            land_value=valuation
        )
        
        run.results["proposals"] = [p.to_dict() for p in proposals]
        print(f"      ✓ Generated {len(proposals)} settlement proposals")
        
        # Create negotiation tasks
        tasks = await self.task_agent.create_tasks_for_state(case_id, "negotiation")
        run.results["tasks_created"] = len(tasks)
        print(f"      ✓ Created {len(tasks)} negotiation tasks")
    
    async def _handle_resolution(self, run: AgentRun, case_id: int):
        """Handle RESOLUTION state automation."""
        print("   📝 Processing RESOLUTION...")
        
        # Generate settlement agreement
        agreement = await self.document_agent.generate_settlement_agreement(
            case_id=case_id,
            party_1_name="Party A",
            party_1_details="resident of Delhi",
            party_2_name="Party B",
            party_2_details="resident of Delhi",
            dispute_subject="land ownership",
            settlement_terms="Division of property as per agreed terms",
            consideration_details="As mutually agreed",
            timeline_details="Completion within 90 days"
        )
        
        if agreement.get("success"):
            run.results["settlement_agreement"] = {
                "generated": True,
                "document_type": "settlement_agreement",
                "cached": agreement.get("cached", False)
            }
            print("      ✓ Settlement agreement generated")
        else:
            run.results["settlement_agreement"] = {"generated": False, "error": agreement.get("error")}
        
        # Create resolution tasks
        tasks = await self.task_agent.create_tasks_for_state(case_id, "resolution")
        run.results["tasks_created"] = len(tasks)
        print(f"      ✓ Created {len(tasks)} resolution tasks")
    
    async def _handle_closure(self, run: AgentRun, case_id: int):
        """Handle CLOSURE state automation."""
        print("   🏁 Processing CLOSURE...")
        
        # Create closure tasks
        tasks = await self.task_agent.create_tasks_for_state(case_id, "closure")
        run.results["tasks_created"] = len(tasks)
        run.results["case_closed"] = True
        print(f"      ✓ Created {len(tasks)} closure tasks")
        print("      ✓ Case closed successfully")
    
    async def transition_case(
        self,
        case_id: int,
        to_state: CaseState,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Transition a case to a new state and run automation.
        """
        state_machine = get_state_machine(case_id)
        
        if not state_machine.can_transition(to_state):
            return {
                "success": False,
                "error": f"Cannot transition from {state_machine.current_state.value} to {to_state.value}",
                "valid_transitions": [s.value for s in state_machine.context.transition_history]
            }
        
        # Perform transition
        success = await state_machine.transition(to_state, reason)
        
        if success:
            # Run automation for new state
            run = await self.run_case_automation(case_id)
            
            return {
                "success": True,
                "new_state": to_state.value,
                "agent_run": run.to_dict()
            }
        
        return {"success": False, "error": "Transition failed"}
    
    def get_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Get agent run by ID."""
        run = self.runs.get(run_id)
        return run.to_dict() if run else None
    
    def get_case_runs(self, case_id: int) -> List[Dict[str, Any]]:
        """Get all runs for a case."""
        return [r.to_dict() for r in self.runs.values() if r.case_id == case_id]


# Singleton instance
_orchestrator: Optional[AgentOrchestrator] = None


def get_orchestrator() -> AgentOrchestrator:
    """Get or create the orchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AgentOrchestrator()
    return _orchestrator
