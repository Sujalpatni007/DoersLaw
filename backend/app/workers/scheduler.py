"""
DOER Platform - Background Scheduler

APScheduler-based worker for processing agent tasks.

FEATURES:
- 5-minute interval processing
- Overdue task checking
- State transition automation
- Agent run monitoring

PRODUCTION UPGRADES:
- Use Celery with Redis broker
- Add distributed locking
- Implement job persistence
- Add monitoring/metrics
"""

from datetime import datetime
from typing import Optional
import asyncio

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.asyncio import AsyncIOExecutor


class AgentScheduler:
    """
    Background scheduler for agent task processing.
    """
    
    def __init__(self, interval_minutes: int = 5):
        """
        Initialize the scheduler.
        
        Args:
            interval_minutes: Interval between job runs
        """
        self.interval_minutes = interval_minutes
        self.scheduler: Optional[AsyncIOScheduler] = None
        self._is_running = False
        self._run_count = 0
    
    def initialize(self):
        """Initialize the APScheduler instance."""
        jobstores = {
            'default': MemoryJobStore()
        }
        
        executors = {
            'default': AsyncIOExecutor()
        }
        
        job_defaults = {
            'coalesce': False,
            'max_instances': 1
        }
        
        self.scheduler = AsyncIOScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults,
            timezone='UTC'
        )
        
        # Add the main processing job
        self.scheduler.add_job(
            self.process_agent_tasks,
            'interval',
            minutes=self.interval_minutes,
            id='agent_task_processor',
            name='Agent Task Processor',
            replace_existing=True
        )
        
        # Add overdue check job (every minute)
        self.scheduler.add_job(
            self.check_overdue_tasks,
            'interval',
            minutes=1,
            id='overdue_checker',
            name='Overdue Task Checker',
            replace_existing=True
        )
        
        print(f"📅 Scheduler initialized with {self.interval_minutes}-minute interval")
    
    def start(self):
        """Start the scheduler."""
        if self.scheduler is None:
            self.initialize()
        
        if not self._is_running:
            self.scheduler.start()
            self._is_running = True
            print("🚀 Background scheduler started")
    
    def stop(self):
        """Stop the scheduler."""
        if self.scheduler and self._is_running:
            self.scheduler.shutdown(wait=False)
            self._is_running = False
            print("⏹️ Background scheduler stopped")
    
    async def process_agent_tasks(self):
        """
        Main job: Process pending agent tasks.
        
        This runs every 5 minutes and handles:
        - Pending task assignments
        - State transition checks
        - Agent run processing
        """
        self._run_count += 1
        print(f"\n{'='*50}")
        print(f"🔄 Agent Task Processing Run #{self._run_count}")
        print(f"   Time: {datetime.utcnow().isoformat()}")
        print(f"{'='*50}")
        
        try:
            # Import agents here to avoid circular imports
            from app.agents.task_agent import get_task_agent
            
            task_agent = get_task_agent()
            pending_tasks = task_agent.get_pending_tasks()
            
            print(f"   📋 Pending tasks: {len(pending_tasks)}")
            
            # Log summary
            for task in pending_tasks[:5]:  # Show first 5
                print(f"      - [{task['priority']}] {task['title']} (Case #{task['case_id']})")
            
            if len(pending_tasks) > 5:
                print(f"      ... and {len(pending_tasks) - 5} more")
            
        except Exception as e:
            print(f"   ❌ Error processing tasks: {e}")
        
        print(f"{'='*50}\n")
    
    async def check_overdue_tasks(self):
        """Check for overdue tasks and send notifications."""
        try:
            from app.agents.task_agent import get_task_agent
            
            task_agent = get_task_agent()
            overdue = await task_agent.check_overdue_tasks()
            
            if overdue:
                print(f"⚠️ Found {len(overdue)} overdue task(s)")
                
        except Exception as e:
            print(f"Error checking overdue: {e}")
    
    def get_status(self) -> dict:
        """Get scheduler status."""
        jobs = []
        if self.scheduler:
            for job in self.scheduler.get_jobs():
                jobs.append({
                    "id": job.id,
                    "name": job.name,
                    "next_run": job.next_run_time.isoformat() if job.next_run_time else None
                })
        
        return {
            "is_running": self._is_running,
            "run_count": self._run_count,
            "interval_minutes": self.interval_minutes,
            "jobs": jobs
        }


# Global scheduler instance
_scheduler: Optional[AgentScheduler] = None


def get_scheduler() -> AgentScheduler:
    """Get or create the scheduler instance."""
    global _scheduler
    if _scheduler is None:
        _scheduler = AgentScheduler(interval_minutes=5)
    return _scheduler


def start_scheduler():
    """Start the global scheduler."""
    scheduler = get_scheduler()
    scheduler.start()


def stop_scheduler():
    """Stop the global scheduler."""
    global _scheduler
    if _scheduler:
        _scheduler.stop()
