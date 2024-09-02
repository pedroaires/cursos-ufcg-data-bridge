import os
from dotenv import load_dotenv

load_dotenv()

broker_url = os.getenv("CELERY_BROKER_URL")
result_backend = os.getenv("CELERY_RESULT_BACKEND")

task_serializer = "json"
result_serializer = "json"
accept_content = ["json"]

timezone = "America/Sao_Paulo"
enable_utc = True

result_expires = 3600

# celery beat config
from celery.schedules import crontab

beat_schedule = {
    'orchestrate-daily-at-4am': {
        'task': 'scripts.orchestrator.orchestrate_tasks',  
        'schedule': crontab(hour=4, minute=0),  # Executa diariamente às 4h
    },
}

# beat_schedule = {
#     'orchestrate-every-minute': {
#         'task': 'scripts.orchestrator.orchestrate_tasks',  
#         'schedule': crontab(minute='*'), 
#     },
# }