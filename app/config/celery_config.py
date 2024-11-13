import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from celery.schedules import crontab

load_dotenv()

# Initialize Celery
broker_url = os.getenv("CELERY_BROKER_URL")
result_backend = os.getenv("CELERY_RESULT_BACKEND")
task_serializer = "json"
result_serializer = "json"
accept_content = ["json"]
timezone = "America/Sao_Paulo"
enable_utc = True
result_expires = 3600
imports = ('core.tasks', 'scripts.orchestrator')


# Setup Scheduler
scheduler_database_url = os.getenv("SCHEDULER_DATABASE_URL", os.getenv("DATABASE_URL"))
engine = create_engine(scheduler_database_url)
beat_dburi = engine.url
beat_scheduler = "sqlalchemy_celery_beat.schedulers:DatabaseScheduler"
beat_schedule = {
    'daily-orchestrate-tasks': {
        'task': 'scripts.orchestrator.orchestrate_tasks',
        'schedule': crontab(hour=4, minute=0),
    },
}
