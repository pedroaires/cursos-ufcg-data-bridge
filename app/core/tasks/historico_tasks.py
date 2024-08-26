from core.celery_app import app
from core.api import APIClient
from config.load_config import settings, load_column_mappings
from core.redis_cache import RedisCache
from core.get_db import get_db
from core.models.historico import Historico
from core.models.disciplina import Disciplina
from core.utils import rename_columns, remove_extra_keys, generate_disciplina_id

import json

api_client = APIClient(
    auth_url=settings.auth_url,
    base_url=settings.base_url,
    username=settings.username,
    password=settings.password
)

redis_cache = RedisCache()


@app.task
def fetch_historicos(previous_task_result=None):
    curriculos_json = redis_cache.get_data("curriculos")
    if not curriculos_json:
        raise Exception("Curriculos não encontrados no cache")
    
    curriculos_json = json.loads(curriculos_json)
    historico_data = []
    
    for curriculo in curriculos_json[:10]:
        cod_curriculo = curriculo['codigo_curriculo']
        cod_curso = curriculo['codigo_curso']
        params = {
            'curriculumCode': cod_curriculo,
            'courseCode': cod_curso,
            'from': '0000.0',
            'to': '9999.9',
            'anonymize': 'true'
        }
        historicos_json = api_client.request('/enrollments', params=params)
        historico_data.extend([{**historico, 'codigo_curriculo': cod_curriculo, 'codigo_curso': cod_curso} for historico in historicos_json])


    print("Dados de HISTORICO coletados com sucesso")
    redis_cache.set_data("historico", json.dumps(historico_data), expire=None)

@app.task
def process_data(previous_task_result=None):
    historico_data_json = redis_cache.get_data("historico")
    if not historico_data_json:
        raise Exception("Dados de HISTORICO não encontrados no cache")

    historico_data = json.loads(historico_data_json)

    historico_mappings = load_column_mappings()['historico']
    
    formatted_historicos = []
    for historico in historico_data:
        formatted_historico = rename_columns(historico, historico_mappings)
        formatted_historico = remove_extra_keys(formatted_historico, historico_mappings)
        formatted_historicos.append(formatted_historico)
    redis_cache.set_data("historico", json.dumps(formatted_historicos), expire=None)


@app.task
def save_data(previous_task_result=None):
    historico_data_json = redis_cache.get_data("historico")
    
    if not historico_data_json:
        raise Exception("Dados de HISTORICO não encontrados no cache")
    
    historico_data = json.loads(historico_data_json)
    
    with get_db() as db:
        valid_historico_data, invalid_historico_data = validate_historico_data( historico_data)
        
        if valid_historico_data:
            insert_valid_data(db, valid_historico_data)
        
        log_invalid_data(invalid_historico_data)

def build_disc_lookup():
    disciplinas_json = redis_cache.get_data("disciplinas")
    if not disciplinas_json:
        raise Exception("Dados de DISCIPLINAS n'ao encontrados no cache")
    disciplinas_data = json.loads(disciplinas_json)
    disciplinas_lookup = {
            disc["id"]: disc
        for disc in disciplinas_data
    }
    return disciplinas_lookup

def validate_historico_data(historico_data):
    disc_lookup = build_disc_lookup()
    valid_historico_data = []
    invalid_historico_data = []
    
    for historico in historico_data:
        cod_disc = historico['codigo_disciplina']
        cod_curr = historico['codigo_curriculo']
        cod_curso = historico['codigo_curso']
        disc_id = generate_disciplina_id(cod_curso, cod_curr, cod_disc)
        if disc_id in disc_lookup:
            valid_historico_data.append(historico)
        else:
            invalid_historico_data.append(historico)
    
    return valid_historico_data, invalid_historico_data
    


def insert_valid_data(db, valid_historico_data):
    try:
        db.bulk_insert_mappings(Historico, valid_historico_data)
        db.commit()
        print(f"{len(valid_historico_data)} registros inseridos com sucesso.")
    except Exception as e:
        db.rollback()
        print(f"Erro ao inserir dados: {e}")
        raise e


def log_invalid_data(invalid_historico_data):
    if invalid_historico_data:
        print(f"Dados inválidos: {invalid_historico_data[:10]}")