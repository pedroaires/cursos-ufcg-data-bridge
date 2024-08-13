from core.celery_app import app
from core.api import APIClient
from core.config import settings
from core.redis_cache import RedisCache
import json
import pandas as pd
api_client = APIClient(
    auth_url=settings.auth_url,
    base_url=settings.base_url,
    username=settings.username,
    password=settings.password
)

redis_cache = RedisCache()

alunos_traducao_colunas = {
    'statusTerm':'periodo_evasao',
    'admissionTerm': 'periodo_ingressao',
    'admissionCode': 'codigo_ingressao',
    'status': 'codigo_evasao',
    'placeOfBirth': 'estado',
    'secondarySchoolType': 'tipo_ensino',
    'affirmativePolicy': 'cotista',
    'age': 'ano_nascimento',
    'gender': 'genero',
}

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

    # Process each student's data
    for i, aluno in enumerate(alunos_data):
        # Rename columns
        for old_key, new_key in alunos_traducao_colunas.items():
            if old_key in aluno:
                aluno[new_key] = aluno.pop(old_key)
        
        # Remove columns not in alunos_traducao_colunas.values() and 'codigo_curso'
        keys_to_remove = set(aluno.keys()) - set(alunos_traducao_colunas.values()) - {'codigo_curso'}
        for key in keys_to_remove:
            aluno.pop(key, None)
        
        aluno['id_aluno'] = i 

    redis_cache.set_data("alunos", json.dumps(alunos_data))
    

@app.task
def save_data(previous_task_result=None):
    alunos_data_json = redis_cache.get_data("alunos")
    if not alunos_data_json:
        raise Exception("Dados de ALUNOS não encontrados no cache")

    alunos_data = json.loads(alunos_data_json)
    alunos_df = pd.DataFrame(alunos_data)
    alunos_df.to_csv('./data/alunos.csv', index=False)
    print("Salvando dados de ALUNOS...")