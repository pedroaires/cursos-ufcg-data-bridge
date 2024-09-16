import logging
import time
import json
import requests
from config.load_config import settings
from core.api import APIClient
from config.load_config import load_column_mappings
from .table_builder import TableBuilder
from core.utils import rename_columns, remove_extra_keys, generate_disciplina_id
from core.models.disciplina import prerequisitos
from core.get_db import get_db
from sqlalchemy import insert
from tqdm import tqdm
from tenacity import retry, stop_after_attempt, retry_if_exception_type, wait_exponential

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PrerequisitosTableBuilder(TableBuilder):

    def _build_impl(self, previous_result):
        disciplinas = previous_result[0]
        prerequisitos_raw = self.fetch_prerequisitos(disciplinas)
        formatted_prerequisitos = self.process_data(prerequisitos_raw)
        self.save_data(formatted_prerequisitos, disciplinas)
        return formatted_prerequisitos
    def get_api_client(self):
        api_client = APIClient(
            auth_url=settings.auth_url,
            base_url=settings.base_url,
            username=settings.username,
            password=settings.password
        )
        return api_client
    
    def get_unique_curso_curriculo(self, disciplinas):
        unique_curso_curriculo = set()
        for disc in disciplinas:
            unique_curso_curriculo.add((disc['codigo_curso'], disc['codigo_curriculo']))
        return unique_curso_curriculo
    def fetch_prerequisitos(self, disciplinas):
        api = self.get_api_client()
        prerequisitos_data = []
        unique_curso_curriculo = self.get_unique_curso_curriculo(disciplinas)
        for (curso, curriculo) in unique_curso_curriculo:
            prerequisitos_json = self.fetch_prerequisitos_by_curso_curriculo(curso, curriculo, api)
            prerequisitos_data.extend(prerequisitos_json)
            
        return prerequisitos_data
    
    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(min=5, max=120),
        retry=retry_if_exception_type(requests.exceptions.RequestException)
    )
    def fetch_prerequisitos_by_curso_curriculo(self, cod_curso, cod_curriculo, api):
        params = {
            'curso': cod_curso,
            'curriculo': cod_curriculo,
        }
        response = api.request("/pre-requisito-disciplinas", params=params)
        if response.status_code != 200:
            logger.error(f"Erro ao buscar dados de prerequisitos do curs: {cod_curso} e curriculo: {cod_curriculo}: {response.status_code}")
            if response.status_code == 500:
                raise(requests.exceptions.RequestException(f"Erro ao buscar prerequisitos do curso: {cod_curso} e curriculo: {cod_curriculo}"))
            return []
        
        prerequisitos_json = response.json()
        if prerequisitos_json is None:
            return []
        return prerequisitos_json
    def add_discs_ids(self, prerequisito):
        cod_disc = prerequisito['codigo_da_disciplina']
        cod_curr = prerequisito['codigo_do_curriculo']
        cod_curso = prerequisito['codigo_do_curso']
        if self.is_tipo_disciplina_cursada(prerequisito['tipo']):
            prerequisito_id = generate_disciplina_id(cod_curso, cod_curr, prerequisito['condicao'])
        else:
            prerequisito_id = None
        disc_id = generate_disciplina_id(cod_curso, cod_curr, cod_disc)
        prerequisito['disciplina_id'] = disc_id
        prerequisito['prerequisito_id'] = prerequisito_id

        return prerequisito
    def process_data(self, prerequisitos_raw):
        prerequisito_mappings = load_column_mappings()['prerequisitos']
        formatted_prerequisitos = []
        for prereq in tqdm(prerequisitos_raw, total=len(prerequisitos_raw), desc="Processing Prerequisitos"):
            formatted_prerequisito = self.add_discs_ids(prereq)
            formatted_prerequisito = rename_columns(formatted_prerequisito, prerequisito_mappings)
            formatted_prerequisito = remove_extra_keys(formatted_prerequisito, prerequisito_mappings)
            formatted_prerequisitos.append(formatted_prerequisito)
        return formatted_prerequisitos
    
    def _build_disc_lookup(self, disciplinas_data):
        disciplinas_lookup = {
                disc["id"]: disc
            for disc in disciplinas_data
        }
        return disciplinas_lookup

    def validate_prereqs_data(self, prereq_data, disciplinas):
        disc_lookup = self._build_disc_lookup(disciplinas)
        valid_prereq_data = []
        invalid_prereq_data = []

        for prereq in tqdm(prereq_data, total=len(prereq_data), desc="Validating Prerequisitos Data"):
            disc_id = prereq['disciplina_id']
            is_valid_prereq = True
            if self.is_tipo_disciplina_cursada(prereq['tipo']):
                is_valid_prereq = self.is_valid_disc(prereq['prerequisito_id'], disc_lookup)
                
            if self.is_valid_disc(disc_id, disc_lookup) and is_valid_prereq:
                valid_prereq_data.append(prereq)
            else:
                invalid_prereq_data.append(prereq)
        
        return valid_prereq_data, invalid_prereq_data
    def is_tipo_disciplina_cursada(self, tipo):
        return tipo.lower() == 'disciplina cursada'.lower()
    def is_valid_disc(self, disc_id, disc_lookup):
        return not disc_lookup.get(disc_id) is None

    def insert_valid_data(self, db, valid_prereq_data):
        try:
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

    def log_invalid_data(self, invalid_prereq_data):
        if invalid_prereq_data:
            print(f"Dados inválidos: {invalid_prereq_data[:10]}")

    def save_data(self, prerequisitos_data, disciplinas):
        with get_db() as db:
            valid_prereqs, invalid_prereqs = self.validate_prereqs_data(prerequisitos_data, disciplinas)
            if valid_prereqs:
                self.insert_valid_data(db, valid_prereqs)
                logger.info("Dados de prerequisitos salvos com sucesso!")
            else:
                print("Nenhum dado válido encontrado.")
            self.log_invalid_data(invalid_prereqs)