from celery import Celery

app = Celery('tasks')
app.config_from_object('config.celery_config')

import core.tasks
import scripts.orchestrator
