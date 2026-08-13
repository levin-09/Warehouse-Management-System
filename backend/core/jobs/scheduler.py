"""Scheduler setup for recurring background jobs.

Uses APScheduler to run the non-AI automation jobs (hourly checks, daily summary,
monthly billing, hourly forecasts).
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from core import logger
from core.jobs.jobs import SchedulerJobs

logging = logger(__name__)

scheduler = AsyncIOScheduler(timezone="UTC")
_jobs = SchedulerJobs()


def start_scheduler() -> None:
    """Register and start all scheduled jobs.

    Returns:
        None
    """
    try:
        scheduler.add_job(_jobs.hourly_checks, "cron", minute="5", id="hourly_checks", replace_existing=True)
        scheduler.add_job(_jobs.hourly_forecasts, "cron", minute="15", id="hourly_forecasts", replace_existing=True)
        scheduler.add_job(_jobs.daily_summary, "cron", hour=8, minute=0, id="daily_summary", replace_existing=True)
        scheduler.add_job(_jobs.monthly_billing, "cron", day=1, hour=0, minute=0, id="monthly_billing", replace_existing=True)
        scheduler.start()
        logging.info("Scheduler started")
    except Exception as error:
        logging.error(f"Failed to start scheduler: {error}")


def shutdown_scheduler() -> None:
    """Stop the scheduler.

    Returns:
        None
    """
    try:
        if scheduler.running:
            scheduler.shutdown(wait=False)
            logging.info("Scheduler stopped")
    except Exception as error:
        logging.error(f"Failed to stop scheduler: {error}")
