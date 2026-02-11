"""
Load Testing with Locust
Simulate 50 concurrent users
"""
from locust import HttpUser, task, between
import random


class DOERPlatformUser(HttpUser):
    """
    Simulated user for load testing
    Target: 50 concurrent users on laptop
    """
    
    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks
    
    def on_start(self):
        """Setup when user starts"""
        self.phone = f"+91-{random.randint(9000000000, 9999999999)}"
        self.case_id = None
    
    @task(3)
    def health_check(self):
        """Check API health - most common task"""
        self.client.get("/api/v1/health")
    
    @task(2)
    def get_cases_list(self):
        """Get list of cases"""
        self.client.get("/api/v1/cases/?skip=0&limit=10")
    
    @task(2)
    def get_land_records(self):
        """Search land records"""
        states = ["Maharashtra", "UP", "Karnataka"]
        self.client.get(f"/api/v1/gov/land-records/search?state={random.choice(states)}&limit=5")
    
    @task(1)
    def verify_land_record(self):
        """Verify a land record"""
        payload = {
            "state": "Maharashtra",
            "district": "Pune",
            "tehsil": "Haveli",
            "village": "Lohegaon",
            "khasra": "123/1",
        }
        self.client.post("/api/v1/gov/verify-land-record", json=payload)
    
    @task(2)
    def simulate_sms(self):
        """Simulate incoming SMS"""
        payload = {
            "phone_number": self.phone,
            "content": random.choice(["Hi", "1", "2", "CASE-2026-10001"]),
        }
        self.client.post("/api/v1/sms/simulate/incoming", json=payload)
    
    @task(1)
    def get_analytics_dashboard(self):
        """Get admin analytics dashboard"""
        self.client.get("/api/v1/analytics/admin/dashboard")
    
    @task(1)
    def get_case_progress(self):
        """Get case progress"""
        case_ids = ["CASE-2026-10001", "CASE-2026-10005", "CASE-2026-10010"]
        self.client.get(f"/api/v1/analytics/case/{random.choice(case_ids)}/progress")


class HighLoadUser(HttpUser):
    """
    High-load user for stress testing
    """
    
    wait_time = between(0.5, 1)  # Faster requests
    
    @task(5)
    def rapid_health_check(self):
        """Rapid health checks"""
        self.client.get("/api/v1/health")
    
    @task(3)
    def rapid_land_search(self):
        """Rapid land record searches"""
        self.client.get("/api/v1/gov/land-records/search?limit=10")
    
    @task(2)
    def rapid_analytics(self):
        """Rapid analytics calls"""
        self.client.get("/api/v1/analytics/admin/funnel")


# Performance baselines (assertions for pytest integration)
PERFORMANCE_BASELINES = {
    "health_check": {"p95_ms": 100, "error_rate": 0.01},
    "land_search": {"p95_ms": 500, "error_rate": 0.02},
    "verify_land": {"p95_ms": 1000, "error_rate": 0.02},
    "sms_simulate": {"p95_ms": 500, "error_rate": 0.01},
    "analytics_dashboard": {"p95_ms": 2000, "error_rate": 0.05},
}


"""
Run with:
    locust -f tests/load/locustfile.py --host=http://localhost:8000 --users=50 --spawn-rate=5

Or headless:
    locust -f tests/load/locustfile.py --host=http://localhost:8000 --users=50 --spawn-rate=5 --run-time=60s --headless
"""
