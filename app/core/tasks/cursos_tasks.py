from core.celery_app import app
from core.api import APIClient
from core.config import settings
from core.redis_cache import RedisCache
from core.get_db import get_db
from core.models.curso import Curso

import os
import pandas as pd
import unidecode
import re
import json

api_client = APIClient(
    auth_url=settings.auth_url,
    base_url=settings.base_url,
    username=settings.username,
    password=settings.password
)

redis_cache = RedisCache()

@app.task
def fetch_cursos():
    cursos = api_client.request("/courses")
    if 'errors' in cursos:
        raise Exception("Ocorreu um erro ao buscar os cursos")
    return cursos

@app.task
def process_data(cursos_json=None):
    print("Processando dados...")
    campus_info = pd.read_csv('./data/campus_info.csv')
    
    # Format the JSON data
    formatted_data = formata_tabela(cursos_json, campus_info)
    
    # Store the processed JSON data in Redis
    redis_cache.set_data("cursos", json.dumps(formatted_data))
    print("Dados processados e colocados no REDIS!")

@app.task
def save_data(previous_task_result=None):
    print("Salvando dados de CURSOS")
    cursos_json = redis_cache.get_data("cursos")
    if not cursos_json:
        raise Exception("Cursos não encontrados no cache")
    
    cursos = json.loads(cursos_json)
    with get_db() as db:
        try:
            db.bulk_insert_mappings(Curso, cursos)
            db.commit()
        except:
            db.rollback()
            raise(Exception("Erro ao salvar dados de cursos no banco de dados"))


def formata_schema_curso(nome_curso, campus_abrev):
    nome_normalizado = unidecode.unidecode(nome_curso).lower()
    nome_formatado = re.sub('[^a-z]+|(?!_)$', '_', nome_normalizado)
    return nome_formatado + campus_abrev.lower()

def get_campus_abrev(course_code, campus_info_df):
    campus_abrev = campus_info_df.loc[campus_info_df['codigo_campus'] == int(course_code[0]), 'campus_abreviado']
    if not campus_abrev.empty:
        return campus_abrev.iloc[0]
    return ''

def formata_tabela(cursos_json, campus_info):
    formatted_cursos = []
    for curso in cursos_json:
        campus_abrev = get_campus_abrev(curso['code'], campus_info)
        nome_schema = formata_schema_curso(curso['name'], campus_abrev)
        
        formatted_curso = {
            'codigo_curso': curso['code'],
            'nome_comum': curso['name'],
            'schema': nome_schema,
            'campus': campus_abrev,
            'disponivel': curso['status'] == 'A'
        }
        formatted_cursos.append(formatted_curso)
    
    return formatted_cursos