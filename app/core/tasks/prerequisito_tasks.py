from core.celery_app import app
from core.api import APIClient
from config.load_config import settings, load_column_mappings
from core.redis_cache import RedisCache
from core.get_db import get_db
from core.models.disciplina import prerequisitos
from core.utils import rename_columns, remove_extra_keys, generate_disciplina_id
from sqlalchemy import insert
from tqdm import tqdm
import json

redis_cache = RedisCache()

@app.task
def fetch_prerequisitos(previous_task_result=None):
    with open("data/PRE_REQUISITOS_DISCIPLINA.json") as f:
        prereqs_data = json.load(f)
    
    redis_cache.set_data("prerequisitos", json.dumps(prereqs_data), expire=None)

@app.task
def process_data(previous_task_result=None):
    prereqs_json = redis_cache.get_data("prerequisitos")
    if not prereqs_json:
        raise Exception("Dados de PREREQUISITOS não encontrados no cache")
    prereqs_data = json.loads(prereqs_json)
    prerequisito_mappings = load_column_mappings()['prerequisitos']
    formatted_prerequisitos = []
    for prereq in tqdm(prereqs_data, total=len(prereqs_data)):
        formatted_prerequisito = rename_columns(prereq, prerequisito_mappings)
        formatted_prerequisito = remove_extra_keys(formatted_prerequisito, prerequisito_mappings)
        formatted_prerequisitos.append(formatted_prerequisito)
    redis_cache.set_data("prerequisitos", json.dumps(formatted_prerequisitos), expire=None)


@app.task
def save_data(previous_task_result=None):
    # Fetch formatted data from cache
    prerequisitos_data_json = redis_cache.get_data("prerequisitos")
    if not prerequisitos_data_json:
        raise Exception("Dados de PREREQUISITOS não encontrados no cache")
    
    prerequisitos_data = json.loads(prerequisitos_data_json)

    with get_db() as db:
        # Fetch ids for the 'prerequisitos'
        valid_prereqs, invalid_prereqs = validate_prereqs_data(prerequisitos_data)

        # Insert valid data into the junction table
        if valid_prereqs:
            insert_valid_data(db, valid_prereqs)
        else:
            print("Nenhum dado válido encontrado.")
        # Log invalid data for further investigation
        log_invalid_data(invalid_prereqs)

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

def validate_prereqs_data(prereq_data):
    disc_lookup = build_disc_lookup()
    valid_prereq_data = []
    invalid_prereq_data = []
    mapped_prereq = set()
    
    for prereq in prereq_data:
        cod_disc = prereq['codigo_disciplina']
        cod_curr = prereq['codigo_curriculo']
        cod_curso = prereq['codigo_curso']
        cod_prereq = prereq['codigo_prerequisito']
        disc_id = generate_disciplina_id(cod_curso, cod_curr, cod_disc)
        prereq_id = generate_disciplina_id(cod_curso, cod_curr, cod_prereq)

        disciplina = disc_lookup.get(disc_id)
        prerequisito = disc_lookup.get(prereq_id)
        if disciplina and prerequisito:
            if (disciplina["id"], prerequisito["id"]) not in mapped_prereq:
                valid_prereq_data.append({
                    "disciplina_id": disciplina["id"],
                    "prerequisito_id": prerequisito["id"]
                })
                mapped_prereq.add((disciplina["id"], prerequisito["id"]))
        else:
            invalid_prereq_data.append(prereq)
    
    return valid_prereq_data, invalid_prereq_data


def insert_valid_data(db, valid_prereq_data):
    try:
        # Use the SQLAlchemy insert function to insert into the junction table
        db.execute(
            insert(prerequisitos),
            valid_prereq_data
        )
        db.commit()
        print(f"{len(valid_prereq_data)} registros inseridos com sucesso.")
    except Exception as e:
        db.rollback()
        print(f"Erro ao inserir dados: {e}")
        raise e

def log_invalid_data(invalid_prereq_data):
    # Log any invalid data for troubleshooting
    if invalid_prereq_data:
        print(f"Dados inválidos: {invalid_prereq_data[:10]}")