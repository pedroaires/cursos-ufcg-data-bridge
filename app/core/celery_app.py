from celery import Celery

app = Celery('tasks')
app.config_from_object('config.celery_config')

import core.tasks.cursos_tasks
import core.tasks.alunos_tasks
import core.tasks.curriculos_tasks
import core.tasks.disciplinas_tasks

app.autodiscover_tasks(['core.tasks'])