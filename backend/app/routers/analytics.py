"""
Analytics Router - User-facing & Admin endpoints
Progress transparency, satisfaction, reports
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from app.services.analytics import get_analytics_service
from app.services.admin_analytics import get_admin_analytics
from app.services.reporting import get_reporting_service

router = APIRouter(prefix="/analytics", tags=["Analytics"])
admin_router = APIRouter(prefix="/analytics/admin", tags=["Admin Analytics"])


# =============================================================================
# Request Models
# =============================================================================

class SurveyRequest(BaseModel):
    case_id: str
    user_id: int
    rating: int  # 1-5
    would_recommend: bool
    feedback: str


# =============================================================================
# User-Facing: Progress Transparency
# =============================================================================

@router.get("/case/{case_id}/progress")
async def get_case_progress(case_id: str):
    """
    Get visual case timeline with completion percentages
    
    Returns:
    - Current phase and completion %
    - Estimated resolution date
    - Milestones timeline
    - Similar cases comparison
    """
    service = get_analytics_service()
    progress = service.get_case_progress(case_id)
    
    return {
        "case_id": progress.case_id,
        "current_phase": progress.current_phase.value,
        "phase_completion": progress.phase_completion,
        "started_at": progress.started_at.isoformat(),
        "estimated_resolution": progress.estimated_resolution.isoformat(),
        "days_remaining": (progress.estimated_resolution - datetime.now()).days,
        "similar_cases_avg_days": progress.similar_cases_avg_days,
        "milestones": progress.milestones,
    }


@router.get("/case/{case_id}/similar")
async def get_similar_cases_stats(case_id: str, case_type: str, state: str = None):
    """Get statistics for similar cases"""
    service = get_analytics_service()
    return service.get_similar_cases_stats(case_type, state)


# =============================================================================
# User-Facing: Satisfaction Tracking
# =============================================================================

@router.post("/survey")
async def submit_satisfaction_survey(request: SurveyRequest):
    """Submit post-resolution satisfaction survey (1-5 rating)"""
    if not 1 <= request.rating <= 5:
        raise HTTPException(status_code=400, detail="Rating must be 1-5")
    
    service = get_analytics_service()
    survey = service.submit_survey(
        case_id=request.case_id,
        user_id=request.user_id,
        rating=request.rating,
        would_recommend=request.would_recommend,
        feedback=request.feedback,
    )
    
    return {
        "survey_id": survey.id,
        "submitted_at": survey.submitted_at.isoformat(),
        "keywords_extracted": survey.keywords,
        "message": "Thank you for your feedback!",
    }


@router.get("/satisfaction/summary")
async def get_satisfaction_summary():
    """Get satisfaction metrics summary"""
    service = get_analytics_service()
    
    return {
        "nps": service.calculate_nps(),
        "rating_distribution": service.get_rating_distribution(),
        "keywords": service.get_keyword_analysis(),
    }


# =============================================================================
# Admin Dashboard
# =============================================================================

@admin_router.post("/demo-data")
async def generate_demo_data(months: int = Query(default=3, le=12)):
    """Generate realistic demo data for testing (3 months default)"""
    service = get_analytics_service()
    return service.generate_demo_data(months)


@admin_router.get("/dashboard")
async def get_admin_dashboard():
    """Get complete admin dashboard data"""
    admin = get_admin_analytics()
    analytics = get_analytics_service()
    
    return {
        "funnel": admin.get_cases_by_status_funnel(),
        "resolution_trends": admin.get_resolution_time_trends(),
        "ai_vs_human": admin.get_ai_vs_human_resolution(),
        "geographic": admin.get_geographic_heatmap(),
        "case_types": admin.get_case_type_distribution(),
        "nps": analytics.calculate_nps(),
        "insights": admin.generate_automated_insights(),
    }


@admin_router.get("/funnel")
async def get_status_funnel():
    """Get cases by status for funnel chart"""
    admin = get_admin_analytics()
    return admin.get_cases_by_status_funnel()


@admin_router.get("/trends")
async def get_resolution_trends(months: int = Query(default=3, le=12)):
    """Get resolution time trends"""
    admin = get_admin_analytics()
    return admin.get_resolution_time_trends(months)


@admin_router.get("/ai-performance")
async def get_ai_vs_human():
    """Get AI vs Human resolution rates"""
    admin = get_admin_analytics()
    return admin.get_ai_vs_human_resolution()


@admin_router.get("/heatmap")
async def get_geographic_heatmap():
    """Get geographic distribution of disputes"""
    admin = get_admin_analytics()
    return admin.get_geographic_heatmap()


@admin_router.get("/leaderboard")
async def get_talent_leaderboard(limit: int = Query(default=10, le=50)):
    """Get talent performance leaderboard"""
    admin = get_admin_analytics()
    return admin.get_talent_leaderboard(limit)


@admin_router.get("/insights")
async def get_automated_insights():
    """Get automated insights from data analysis"""
    admin = get_admin_analytics()
    return {"insights": admin.generate_automated_insights()}


# =============================================================================
# Reporting
# =============================================================================

@admin_router.get("/report/summary")
async def get_monthly_summary(month: int = None, year: int = None):
    """Get monthly case summary data"""
    reporting = get_reporting_service()
    return reporting.generate_monthly_summary(month, year)


@admin_router.post("/report/pdf")
async def generate_pdf_report(month: int = None, year: int = None):
    """Generate monthly PDF report"""
    reporting = get_reporting_service()
    filepath = reporting.export_pdf_report(month, year)
    
    return {
        "filepath": filepath,
        "download_url": f"/api/v1/analytics/admin/download?file={filepath.split('/')[-1]}",
    }


@admin_router.post("/report/excel")
async def generate_excel_report(month: int = None, year: int = None):
    """Generate monthly Excel report"""
    reporting = get_reporting_service()
    filepath = reporting.export_excel_report(month, year)
    
    return {
        "filepath": filepath,
        "download_url": f"/api/v1/analytics/admin/download?file={filepath.split('/')[-1]}",
    }


@admin_router.get("/download")
async def download_report(file: str):
    """Download generated report file"""
    import os
    
    output_dir = "/tmp/doer_reports"
    filepath = os.path.join(output_dir, file)
    
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Report not found")
    
    return FileResponse(filepath, filename=file)


@admin_router.get("/reports")
async def list_reports():
    """List available report files"""
    reporting = get_reporting_service()
    return {"reports": reporting.get_report_files()}
