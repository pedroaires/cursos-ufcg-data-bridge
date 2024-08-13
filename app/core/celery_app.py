from celery import Celery
from core.config import settings

app = Celery('tasks')
app.config_from_object('celery_config')

import core.tasks.cursos_tasks
import core.tasks.alunos_tasks
import core.tasks.curriculos_tasks

app.autodiscover_tasks(['core.tasks'])