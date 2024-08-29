from core.celery_app import app
from core.api import APIClient
from config.load_config import settings, load_column_mappings
from core.redis_cache import RedisCache
from core.get_db import get_db
from core.models.disciplina import Disciplina
from core.utils import rename_columns, remove_extra_keys

import json

api_client = APIClient(
    auth_url=settings.auth_url,
    base_url=settings.base_url,
    username=settings.username,
    password=settings.password
)

redis_cache = RedisCache()

@app.task
def fetch_disciplinas(previous_task_result=None):
    curriculos_json = redis_cache.get_data("curriculos")
    if not curriculos_json:
        raise Exception("Curriculos não encontrados no cache")
    
    curriculos_json = json.loads(curriculos_json)
    disciplinas_data = []
    
    for curriculo in curriculos_json[:10]:
        cod_curriculo = curriculo['codigo_curriculo']
        cod_curso = curriculo['codigo_curso']
        params = {
            'curriculumCode': cod_curriculo,
            'courseCode': cod_curso
        }
        disciplinas_json = api_client.request('/course/getSubjectsPerCurriculum', params=params)
        disciplinas_data = disciplinas_data + disciplinas_json
    redis_cache.set_data("disciplinas", json.dumps(disciplinas_data), expire=None)

@app.task
def process_data(previous_task_result=None):
    disciplinas_data_json = redis_cache.get_data("disciplinas")
    if not disciplinas_data_json:
        raise Exception("Dados de DISCIPLINAS não encontrados no cache")

    disciplinas_data = json.loads(disciplinas_data_json)

    disciplina_mappings = load_column_mappings()['disciplinas']
    
    formatted_disciplinas = []
    for disciplina in disciplinas_data:
        formatted_disciplina = rename_columns(disciplina, disciplina_mappings)
        formatted_disciplina = remove_extra_keys(formatted_disciplina, disciplina_mappings)
        formatted_disciplina['id'] = generate_disc_id(formatted_disciplina['codigo_curso'], formatted_disciplina['codigo_curriculo'], formatted_disciplina['codigo_disciplina'])
        formatted_disciplinas.append(formatted_disciplina)
    redis_cache.set_data("disciplinas", json.dumps(formatted_disciplinas), expire=None)

def generate_disc_id(cod_curso, cod_curr, cod_disc):
    return f"{cod_curso}-{cod_curr}-{cod_disc}"

@app.task
def save_data(previoes_task_result=None):
    disciplinas_data_json = redis_cache.get_data("disciplinas")
    if not disciplinas_data_json:
        raise Exception("Dados de DISCIPLINAS não encontrados no cache")

    disciplinas_data = json.loads(disciplinas_data_json)

    with get_db() as db:
        try:
            db.bulk_insert_mappings(Disciplina, disciplinas_data)
            db.commit()
        except:
            db.rollback()
            raise(Exception("Erro ao salvar dados de disciplinas no banco de dados"))