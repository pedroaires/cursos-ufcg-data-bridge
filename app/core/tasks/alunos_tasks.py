from core.celery_app import app
from core.api import APIClient
from config.load_config import settings, load_column_mappings
from core.redis_cache import RedisCache
from core.get_db import get_db
from core.models.aluno import Aluno
from core.utils import rename_columns, remove_extra_keys

import json
import pandas as pd
api_client = APIClient(
    auth_url=settings.auth_url,
    base_url=settings.base_url,
    username=settings.username,
    password=settings.password
)

redis_cache = RedisCache()

@app.task
def fetch_alunos(previous_task_result=None):
    cursos_json = redis_cache.get_data("cursos")
    if not cursos_json:
        raise Exception("Cursos não encontrados no cache")
    
    cursos = json.loads(cursos_json)
    alunos_data = []

    for curso in cursos:
        if curso['disponivel']:
            params = {
                'courseCode': curso['codigo_curso'],
                'from': '0000.0',
                'to': '9999.9',
                'anonymize': 'true'
            }
            alunos_json = api_client.request('/students', params=params)
            if 'students' in alunos_json:
                for aluno in alunos_json['students']:
                    aluno['codigo_curso'] = curso['codigo_curso']
                    alunos_data.append(aluno)
            else:
                print(f"Error on course {curso['codigo_curso']}")
                print(alunos_json)
    
    redis_cache.set_data("alunos", json.dumps(alunos_data), expire=None)

@app.task
def process_data(previous_task_result=None):
    alunos_data_json = redis_cache.get_data("alunos")
    if not alunos_data_json:
        raise Exception("Dados de ALUNOS não encontrados no cache")

    alunos_data = json.loads(alunos_data_json)

    aluno_mappings = load_column_mappings()['alunos']
    
    for aluno in alunos_data:
        formatted_aluno = rename_columns(aluno, aluno_mappings)
        formatted_aluno = remove_extra_keys(formatted_aluno, aluno_mappings)

    redis_cache.set_data("alunos", json.dumps(alunos_data))
    

@app.task
def save_data(previous_task_result=None):
    print("Salvando dados de ALUNOS")
    alunos_data_json = redis_cache.get_data("alunos")
    if not alunos_data_json:
        raise Exception("Dados de ALUNOS não encontrados no cache")

    alunos_data = json.loads(alunos_data_json)
    with get_db() as db:
        try:
            db.bulk_insert_mappings(Aluno, alunos_data)
            db.commit()
        except:
            db.rollback()
            raise(Exception("Erro ao salvar dados de alunos no banco de dados"))