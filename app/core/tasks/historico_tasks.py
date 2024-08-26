from core.celery_app import app
from core.api import APIClient
from config.load_config import settings, load_column_mappings
from core.redis_cache import RedisCache
from core.get_db import get_db
from core.models.historico import Historico
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

# @app.task
# def save_data(previous_task_result=None):
#     historico_data_json = redis_cache.get_data("historico")
#     if not historico_data_json:
#         raise Exception("Dados de HISTORICO não encontrados no cache")
    
#     historico_data = json.loads(historico_data_json)

#     with get_db() as db:
#         try:
#             db.bulk_insert_mappings(Historico, historico_data)
#             db.commit()
#         except Exception as e:
#             print(e)
#             db.rollback()
#             raise e

@app.task
def save_data(previous_task_result=None):
    historico_data_json = redis_cache.get_data("historico")
    
    if not historico_data_json:
        raise Exception("Dados de HISTORICO não encontrados no cache")
    
    historico_data = json.loads(historico_data_json)
    
    with get_db() as db:
        valid_historico_data, invalid_historico_data = validate_historico_data(db, historico_data)
        
        if valid_historico_data:
            insert_valid_data(db, valid_historico_data)
        
        log_invalid_data(invalid_historico_data)

# Helper function to validate historico data
def validate_historico_data(db, historico_data):
    valid_historico_data = []
    invalid_historico_data = []
    
    for historico in historico_data:
        if is_valid_foreign_key(db, historico):
            valid_historico_data.append(historico)
        else:
            invalid_historico_data.append(historico)
    
    return valid_historico_data, invalid_historico_data

# Helper function to check foreign key validity
def is_valid_foreign_key(db, historico):
    return db.query(Disciplina).filter_by(
        codigo_curriculo=historico.get('codigo_curriculo'),
        codigo_curso=historico.get('codigo_curso'),
        codigo_disciplina=historico.get('codigo_disciplina')
    ).first() is not None

# Helper function to insert valid data
def insert_valid_data(db, valid_historico_data):
    try:
        db.bulk_insert_mappings(Historico, valid_historico_data)
        db.commit()
        print(f"{len(valid_historico_data)} registros inseridos com sucesso.")
    except Exception as e:
        db.rollback()
        print(f"Erro ao inserir dados: {e}")
        raise e

# Helper function to log invalid data
def log_invalid_data(invalid_historico_data):
    if invalid_historico_data:
        for invalid_data in invalid_historico_data:
            print(f"Dados inválidos: {invalid_data}")