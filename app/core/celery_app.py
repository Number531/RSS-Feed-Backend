"""
Celery application configuration for RSS feed tasks.
"""

from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

# Create Celery app
celery_app = Celery(
    "rss_feed_worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks.rss_tasks"],
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600,  # 10 minutes max per task
    task_soft_time_limit=540,  # 9 minutes soft limit
    worker_prefetch_multiplier=1,  # Fetch one task at a time
    worker_max_tasks_per_child=50,  # Restart worker after 50 tasks
)

# Celery Beat schedule - RSS feed fetching every 15 minutes
celery_app.conf.beat_schedule = {
    "fetch-all-rss-feeds": {
        "task": "app.tasks.rss_tasks.fetch_all_feeds",
        "schedule": settings.CELERY_BEAT_SCHEDULE_INTERVAL,  # 900 seconds = 15 minutes
        "options": {"expires": 840},  # Expire after 14 minutes if not executed
    },
}
