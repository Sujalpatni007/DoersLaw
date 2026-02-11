"""
Admin Dashboard Analytics
Funnel charts, trends, geographic heatmap, talent leaderboard
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import Counter, defaultdict
import random
import logging

from app.services.analytics import get_analytics_service, CasePhase

logger = logging.getLogger("ADMIN_ANALYTICS")


class AdminDashboardAnalytics:
    """
    Admin analytics dashboard features
    """
    
    def __init__(self):
        self.analytics = get_analytics_service()
    
    def get_cases_by_status_funnel(self) -> Dict:
        """Get cases by status for funnel chart"""
        cases = self.analytics.demo_cases
        
        status_counts = Counter(c["phase"] for c in cases)
        
        # Order for funnel
        funnel_order = ["intake", "verification", "analysis", "negotiation", "resolution", "closed"]
        
        funnel_data = []
        for phase in funnel_order:
            count = status_counts.get(phase, 0)
            funnel_data.append({
                "phase": phase,
                "label": phase.replace("_", " ").title(),
                "count": count,
                "percentage": round(count / len(cases) * 100, 1) if cases else 0,
            })
        
        return {
            "funnel": funnel_data,
            "total_cases": len(cases),
            "active_cases": sum(1 for c in cases if c["phase"] != "closed"),
            "closed_cases": status_counts.get("closed", 0),
        }
    
    def get_resolution_time_trends(self, months: int = 3) -> Dict:
        """Get resolution time trends over time"""
        cases = [c for c in self.analytics.demo_cases if c["phase"] == "closed"]
        
        # Group by month
        monthly_data = defaultdict(list)
        for case in cases:
            if case.get("resolved_at"):
                start = datetime.fromisoformat(case["started_at"])
                end = datetime.fromisoformat(case["resolved_at"])
                resolution_days = (end - start).days
                month_key = end.strftime("%Y-%m")
                monthly_data[month_key].append(resolution_days)
        
        trends = []
        for month, times in sorted(monthly_data.items()):
            avg = sum(times) / len(times) if times else 0
            trends.append({
                "month": month,
                "avg_resolution_days": round(avg, 1),
                "min_days": min(times) if times else 0,
                "max_days": max(times) if times else 0,
                "cases_resolved": len(times),
            })
        
        # Calculate improvement
        if len(trends) >= 2:
            first_avg = trends[0]["avg_resolution_days"]
            last_avg = trends[-1]["avg_resolution_days"]
            improvement = round((first_avg - last_avg) / first_avg * 100, 1) if first_avg else 0
        else:
            improvement = 0
        
        return {
            "trends": trends,
            "improvement_pct": improvement,
            "trend_direction": "improving" if improvement > 0 else "stable",
        }
    
    def get_ai_vs_human_resolution(self) -> Dict:
        """Get AI vs Human resolution rates"""
        cases = [c for c in self.analytics.demo_cases if c["phase"] == "closed"]
        
        ai_resolved = sum(1 for c in cases if c.get("resolved_by") == "ai")
        human_resolved = sum(1 for c in cases if c.get("resolved_by") == "human")
        total = len(cases)
        
        # Calculate efficiency
        ai_cases = [c for c in cases if c.get("resolved_by") == "ai"]
        human_cases = [c for c in cases if c.get("resolved_by") == "human"]
        
        def avg_resolution(case_list):
            times = []
            for c in case_list:
                if c.get("resolved_at"):
                    start = datetime.fromisoformat(c["started_at"])
                    end = datetime.fromisoformat(c["resolved_at"])
                    times.append((end - start).days)
            return sum(times) / len(times) if times else 0
        
        return {
            "ai_resolved": ai_resolved,
            "human_resolved": human_resolved,
            "ai_percentage": round(ai_resolved / total * 100, 1) if total else 0,
            "human_percentage": round(human_resolved / total * 100, 1) if total else 0,
            "ai_avg_days": round(avg_resolution(ai_cases), 1),
            "human_avg_days": round(avg_resolution(human_cases), 1),
            "ai_efficiency_gain": round((avg_resolution(human_cases) - avg_resolution(ai_cases)) / avg_resolution(human_cases) * 100, 1) if avg_resolution(human_cases) else 0,
        }
    
    def get_geographic_heatmap(self) -> Dict:
        """Get geographic distribution of disputes"""
        cases = self.analytics.demo_cases
        
        state_counts = Counter(c["state"] for c in cases)
        district_counts = Counter(f"{c['state']}:{c['district']}" for c in cases)
        
        # State-level data
        state_data = []
        for state, count in state_counts.most_common():
            state_data.append({
                "state": state,
                "count": count,
                "percentage": round(count / len(cases) * 100, 1),
                "intensity": min(1.0, count / (len(cases) * 0.3)),  # Normalized intensity
            })
        
        # District-level data
        district_data = []
        for district_key, count in district_counts.most_common(10):
            state, district = district_key.split(":")
            district_data.append({
                "state": state,
                "district": district,
                "count": count,
            })
        
        # Case type by region
        type_by_state = defaultdict(lambda: Counter())
        for case in cases:
            type_by_state[case["state"]][case["type"]] += 1
        
        regional_trends = []
        for state, type_counts in type_by_state.items():
            top_type = type_counts.most_common(1)[0] if type_counts else ("unknown", 0)
            regional_trends.append({
                "state": state,
                "dominant_case_type": top_type[0].replace("_", " ").title(),
                "count": top_type[1],
            })
        
        return {
            "state_heatmap": state_data,
            "top_districts": district_data,
            "regional_trends": regional_trends,
        }
    
    def get_talent_leaderboard(self, limit: int = 10) -> Dict:
        """Get talent performance leaderboard"""
        cases = self.analytics.demo_cases
        
        # Calculate metrics per talent
        talent_metrics = defaultdict(lambda: {
            "cases_handled": 0,
            "cases_resolved": 0,
            "total_resolution_days": 0,
            "ratings": [],
        })
        
        for case in cases:
            talent_id = case.get("talent_id")
            if talent_id:
                talent_metrics[talent_id]["cases_handled"] += 1
                if case["phase"] == "closed":
                    talent_metrics[talent_id]["cases_resolved"] += 1
                    if case.get("resolved_at"):
                        start = datetime.fromisoformat(case["started_at"])
                        end = datetime.fromisoformat(case["resolved_at"])
                        talent_metrics[talent_id]["total_resolution_days"] += (end - start).days
        
        # Add ratings from surveys
        for survey in self.analytics.surveys.values():
            case = next((c for c in cases if c["id"] == survey.case_id), None)
            if case and case.get("talent_id"):
                talent_metrics[case["talent_id"]]["ratings"].append(survey.rating)
        
        # Calculate scores and build leaderboard
        leaderboard = []
        for talent_id, metrics in talent_metrics.items():
            resolved = metrics["cases_resolved"]
            avg_days = metrics["total_resolution_days"] / resolved if resolved else 0
            ratings = metrics["ratings"]
            avg_rating = sum(ratings) / len(ratings) if ratings else 0
            
            # Composite score
            resolution_score = min(100, (1 / max(1, avg_days / 30)) * 50) if resolved else 0
            rating_score = (avg_rating / 5) * 30 if ratings else 0
            volume_score = min(20, metrics["cases_handled"] * 2)
            
            total_score = resolution_score + rating_score + volume_score
            
            leaderboard.append({
                "talent_id": talent_id,
                "name": f"Adv. {['Sharma', 'Kulkarni', 'Rao', 'Patel', 'Singh', 'Kumar', 'Devi', 'Reddy', 'Naidu', 'Verma'][talent_id % 10]}",
                "cases_handled": metrics["cases_handled"],
                "cases_resolved": resolved,
                "avg_resolution_days": round(avg_days, 1),
                "avg_rating": round(avg_rating, 2),
                "score": round(total_score, 1),
            })
        
        leaderboard.sort(key=lambda x: x["score"], reverse=True)
        
        return {
            "leaderboard": leaderboard[:limit],
            "total_talent": len(talent_metrics),
            "top_performer": leaderboard[0] if leaderboard else None,
        }
    
    def get_case_type_distribution(self) -> Dict:
        """Get distribution of case types"""
        cases = self.analytics.demo_cases
        type_counts = Counter(c["type"] for c in cases)
        
        distribution = []
        for case_type, count in type_counts.most_common():
            distribution.append({
                "type": case_type,
                "label": case_type.replace("_", " ").title(),
                "count": count,
                "percentage": round(count / len(cases) * 100, 1),
            })
        
        return {
            "distribution": distribution,
            "total": len(cases),
        }
    
    def generate_automated_insights(self) -> List[Dict]:
        """Generate automated insights from data"""
        insights = []
        cases = self.analytics.demo_cases
        
        if not cases:
            return [{"type": "info", "message": "No data available for insights"}]
        
        # Case type trends
        recent = [c for c in cases if datetime.fromisoformat(c["started_at"]) > datetime.now() - timedelta(days=30)]
        older = [c for c in cases if datetime.fromisoformat(c["started_at"]) <= datetime.now() - timedelta(days=30)]
        
        recent_types = Counter(c["type"] for c in recent)
        older_types = Counter(c["type"] for c in older)
        
        for case_type in recent_types:
            recent_count = recent_types[case_type]
            older_count = older_types.get(case_type, 1)
            change = ((recent_count - older_count) / older_count) * 100 if older_count else 0
            
            if change > 20:
                insights.append({
                    "type": "warning",
                    "category": "trend",
                    "message": f"{case_type.replace('_', ' ').title()} cases up {int(change)}% this month",
                    "severity": "high" if change > 50 else "medium",
                })
            elif change < -20:
                insights.append({
                    "type": "success",
                    "category": "trend",
                    "message": f"{case_type.replace('_', ' ').title()} cases down {int(abs(change))}% this month",
                    "severity": "low",
                })
        
        # Resolution efficiency
        ai_data = self.get_ai_vs_human_resolution()
        if ai_data["ai_efficiency_gain"] > 15:
            insights.append({
                "type": "success",
                "category": "efficiency",
                "message": f"AI resolving cases {int(ai_data['ai_efficiency_gain'])}% faster than human average",
                "severity": "low",
            })
        
        # NPS insight
        nps_data = self.analytics.calculate_nps()
        if nps_data["nps"] > 50:
            insights.append({
                "type": "success",
                "category": "satisfaction",
                "message": f"NPS score of {int(nps_data['nps'])} - Excellent customer satisfaction",
                "severity": "low",
            })
        elif nps_data["nps"] < 0:
            insights.append({
                "type": "warning",
                "category": "satisfaction",
                "message": f"NPS score of {int(nps_data['nps'])} - Customer satisfaction needs attention",
                "severity": "high",
            })
        
        return insights


# Singleton
_admin_analytics: Optional[AdminDashboardAnalytics] = None

def get_admin_analytics() -> AdminDashboardAnalytics:
    global _admin_analytics
    if _admin_analytics is None:
        _admin_analytics = AdminDashboardAnalytics()
    return _admin_analytics
