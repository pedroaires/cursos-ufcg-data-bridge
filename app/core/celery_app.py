from celery import Celery

app = Celery('tasks')
app.config_from_object('config.celery_config')

import core.table_tasks

app.autodiscover_tasks(['core.tasks'])