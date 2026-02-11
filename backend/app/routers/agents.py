"""
DOER Platform - Agents API Router

Endpoints for agent orchestration and case automation.

ENDPOINTS:
- POST /agents/run/{case_id} - Trigger agent run
- GET /agents/status/{run_id} - Check run status
- POST /agents/transition/{case_id} - Manual state transition
- GET /agents/timeline/{case_id} - Generate timeline
- GET /agents/proposals/{case_id} - Get settlement proposals
- GET /agents/tasks/{case_id} - Get case tasks
- GET /agents/scheduler/status - Scheduler status
- POST /agents/scheduler/start - Start scheduler
"""

from typing import Optional, List

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.agents.state_machine import CaseState, get_state_machine, create_state_machine
from app.agents.orchestrator import get_orchestrator
from app.agents.timeline_agent import get_timeline_agent
from app.agents.task_agent import get_task_agent
from app.agents.negotiation_agent import get_negotiation_agent, Claim
from app.workers.scheduler import get_scheduler


router = APIRouter(prefix="/agents", tags=["Agent Automation"])


# ============================================================================
# Request/Response Schemas
# ============================================================================

class RunAgentRequest(BaseModel):
    """Request to run agent automation."""
    dispute_type: str = Field(default="ownership_dispute", description="Type of dispute")
    complexity: str = Field(default="medium", description="Complexity level")
    location: str = Field(default="delhi", description="Location for valuation")
    area_acres: float = Field(default=1.0, description="Land area in acres")


class TransitionRequest(BaseModel):
    """Request to transition case state."""
    to_state: str = Field(..., description="Target state")
    reason: Optional[str] = Field(None, description="Transition reason")


class TimelineRequest(BaseModel):
    """Request to generate timeline."""
    dispute_type: str = Field(default="ownership_dispute")
    complexity: str = Field(default="medium")
    location_type: str = Field(default="urban")


class NegotiationRequest(BaseModel):
    """Request to generate settlement proposals."""
    party_1_name: str = Field(default="Party A")
    party_1_percentage: float = Field(default=50)
    party_1_years: int = Field(default=10)
    party_1_docs: int = Field(default=3)
    party_2_name: str = Field(default="Party B")
    party_2_percentage: float = Field(default=50)
    party_2_years: int = Field(default=10)
    party_2_docs: int = Field(default=3)
    area_acres: float = Field(default=1.0)
    location: str = Field(default="delhi")


# ============================================================================
# Agent Run Endpoints
# ============================================================================

@router.post("/run/{case_id}")
async def run_agent_automation(case_id: int, request: RunAgentRequest):
    """
    Trigger agent automation for a case.
    
    This runs all appropriate agents based on the case's current state.
    """
    orchestrator = get_orchestrator()
    
    # Ensure state machine exists
    create_state_machine(case_id)
    
    run = await orchestrator.run_case_automation(
        case_id=case_id,
        dispute_type=request.dispute_type,
        complexity=request.complexity,
        location=request.location,
        area_acres=request.area_acres,
        triggered_by="api"
    )
    
    return run.to_dict()


@router.get("/status/{run_id}")
async def get_run_status(run_id: str):
    """Get the status of an agent run."""
    orchestrator = get_orchestrator()
    
    run = orchestrator.get_run(run_id)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run not found: {run_id}"
        )
    
    return run


@router.get("/runs/{case_id}")
async def get_case_runs(case_id: int):
    """Get all agent runs for a case."""
    orchestrator = get_orchestrator()
    return {
        "case_id": case_id,
        "runs": orchestrator.get_case_runs(case_id)
    }


# ============================================================================
# State Machine Endpoints
# ============================================================================

@router.get("/state/{case_id}")
async def get_case_state(case_id: int):
    """Get current state of a case."""
    try:
        machine = get_state_machine(case_id)
        return machine.get_state_info()
    except Exception:
        # Create new state machine if doesn't exist
        machine = create_state_machine(case_id)
        return machine.get_state_info()


@router.post("/transition/{case_id}")
async def transition_case_state(case_id: int, request: TransitionRequest):
    """
    Manually transition a case to a new state.
    
    This will run automation for the new state.
    """
    try:
        to_state = CaseState(request.to_state)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid state: {request.to_state}. Valid states: {[s.value for s in CaseState]}"
        )
    
    orchestrator = get_orchestrator()
    result = await orchestrator.transition_case(
        case_id=case_id,
        to_state=to_state,
        reason=request.reason
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Transition failed")
        )
    
    return result


# ============================================================================
# Timeline Endpoints
# ============================================================================

@router.post("/timeline/{case_id}")
async def generate_timeline(case_id: int, request: TimelineRequest):
    """Generate a timeline for a case."""
    agent = get_timeline_agent()
    
    timeline = agent.generate_timeline(
        case_id=case_id,
        dispute_type=request.dispute_type,
        complexity=request.complexity,
        location_type=request.location_type
    )
    
    return timeline


# ============================================================================
# Task Endpoints
# ============================================================================

@router.get("/tasks/{case_id}")
async def get_case_tasks(case_id: int):
    """Get all tasks for a case."""
    agent = get_task_agent()
    tasks = agent.get_case_tasks(case_id)
    
    return {
        "case_id": case_id,
        "task_count": len(tasks),
        "tasks": tasks
    }


@router.get("/tasks/pending")
async def get_pending_tasks():
    """Get all pending tasks across all cases."""
    agent = get_task_agent()
    tasks = agent.get_pending_tasks()
    
    return {
        "count": len(tasks),
        "tasks": tasks
    }


@router.get("/notifications")
async def get_notifications(limit: int = Query(20, ge=1, le=100)):
    """Get recent notifications."""
    agent = get_task_agent()
    notifications = agent.get_notifications(limit)
    
    return {
        "count": len(notifications),
        "notifications": notifications
    }


# ============================================================================
# Negotiation Endpoints
# ============================================================================

@router.post("/proposals/{case_id}")
async def generate_proposals(case_id: int, request: NegotiationRequest):
    """Generate settlement proposals for a case."""
    agent = get_negotiation_agent()
    
    party_1 = Claim(
        party_name=request.party_1_name,
        claimed_percentage=request.party_1_percentage,
        years_of_possession=request.party_1_years,
        supporting_documents=request.party_1_docs
    )
    
    party_2 = Claim(
        party_name=request.party_2_name,
        claimed_percentage=request.party_2_percentage,
        years_of_possession=request.party_2_years,
        supporting_documents=request.party_2_docs
    )
    
    valuation = agent.estimate_land_value(
        area_acres=request.area_acres,
        location=request.location
    )
    
    proposals = agent.generate_proposals(
        case_id=case_id,
        dispute_type="ownership_dispute",
        party_1=party_1,
        party_2=party_2,
        land_value=valuation
    )
    
    return {
        "case_id": case_id,
        "valuation": valuation,
        "proposal_count": len(proposals),
        "proposals": [p.to_dict() for p in proposals]
    }


@router.get("/proposals/{case_id}/list")
async def list_case_proposals(case_id: int):
    """List all proposals for a case."""
    agent = get_negotiation_agent()
    proposals = agent.get_case_proposals(case_id)
    
    return {
        "case_id": case_id,
        "proposals": proposals
    }


@router.get("/valuation")
async def estimate_land_value(
    area_acres: float = Query(1.0, description="Land area in acres"),
    location: str = Query("delhi", description="Location"),
    land_type: str = Query("agricultural", description="Type of land")
):
    """Get land value estimation."""
    agent = get_negotiation_agent()
    
    valuation = agent.estimate_land_value(
        area_acres=area_acres,
        location=location,
        land_type=land_type
    )
    
    return valuation


# ============================================================================
# Scheduler Endpoints
# ============================================================================

@router.get("/scheduler/status")
async def get_scheduler_status():
    """Get background scheduler status."""
    scheduler = get_scheduler()
    return scheduler.get_status()


@router.post("/scheduler/start")
async def start_background_scheduler():
    """Start the background scheduler."""
    scheduler = get_scheduler()
    scheduler.start()
    
    return {
        "message": "Scheduler started",
        "status": scheduler.get_status()
    }


@router.post("/scheduler/stop")
async def stop_background_scheduler():
    """Stop the background scheduler."""
    scheduler = get_scheduler()
    scheduler.stop()
    
    return {
        "message": "Scheduler stopped",
        "status": scheduler.get_status()
    }
