from core.celery_app import app
from core.api import APIClient
from config.load_config import settings, load_column_mappings
from core.redis_cache import RedisCache
from core.utils import rename_columns, remove_extra_keys
from core.get_db import get_db
from core.models.curriculo import Curriculo
from tqdm import tqdm
import json
api_client = APIClient(
    auth_url=settings.auth_url,
    base_url=settings.base_url,
    username=settings.username,
    password=settings.password
)

redis_cache = RedisCache()

def fetch_curriculos_list(codigo_curso):
    params = {"courseCode": codigo_curso}
    curriculos_json = api_client.request("/course/getActivesCurriculum", params=params)
    if 'errors' in curriculos_json:
        print("Rota nao retornou o curriculo corretamente, tentando outra rota...")
        curriculos_json = api_client.request("/course/getCurriculumCodes", params=params)
    return curriculos_json

def fetch_curriculos_info(codigo_curso, codigo_curriculo):
    params = {"courseCode": codigo_curso, "curriculumCode": codigo_curriculo}
    curriculo_info_json = api_client.request("/course/getCurriculum", params=params)
    return curriculo_info_json


    

@app.task
def fetch_curriculos(previous_task_result=None):
    cursos_json = redis_cache.get_data("cursos")
    if not cursos_json:
        raise Exception("Cursos não encontrados no cache")
    
    cursos = json.loads(cursos_json)
    curriculos_data = []
    for curso in tqdm(cursos[:10], total=len(cursos[:10])):
        if curso['disponivel']:
            curriculos_json = fetch_curriculos_list(curso['codigo_curso'])
            for curr_dict in curriculos_json:
                cod_curriculo = curr_dict['curriculumCode']
                curriculo_info_json = fetch_curriculos_info(curso['codigo_curso'], cod_curriculo)
                curriculo_info_json['codigo_curso'] = curso['codigo_curso']
                curriculo_info_json['codigo_curriculo'] = cod_curriculo
                curriculos_data.append(curriculo_info_json)
    redis_cache.set_data("curriculos", json.dumps(curriculos_data), expire=None)
    

@app.task
def process_data(previous_task_result=None):
    curriculos_data_json = redis_cache.get_data("curriculos")
    if not curriculos_data_json:
        raise Exception("Dados de CURRICULOS não encontrados no cache")
    
    curriculos_data = json.loads(curriculos_data_json)

    curriculo_mappings = load_column_mappings()['curriculos']
    print("Processando dados de CURRICULOS...")
    formatted_curriculos = []
    for curriculo in curriculos_data:
        formatted_curriculo = rename_columns(curriculo, curriculo_mappings)
        formatted_curriculo = remove_extra_keys(curriculo, curriculo_mappings)
        formatted_curriculos.append(formatted_curriculo)
    redis_cache.set_data("curriculos", json.dumps(formatted_curriculos))
    print("Dados de CURRICULOS processados!")

@app.task
def save_data(previous_task_result=None):
    print("Salvando dados de CURRICULOS")
    curriculos_data_json = redis_cache.get_data("curriculos")
    if not curriculos_data_json:
        raise Exception("Dados de CURRICULOS não encontrados no cache")
    curriculos_data = json.loads(curriculos_data_json)
    with get_db() as db:
        try:
            db.bulk_insert_mappings(Curriculo, curriculos_data)
            db.commit()
        except:
            db.rollback()
            raise(Exception("Erro ao salvar dados de curriculos no banco de dados"))