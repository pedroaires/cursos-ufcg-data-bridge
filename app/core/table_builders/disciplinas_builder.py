import logging
import requests
from config.load_config import settings
from core.api import APIClient
from config.load_config import load_column_mappings
from .table_builder import TableBuilder
from core.utils import rename_columns, remove_extra_keys, generate_disciplina_id
from core.models.disciplina import Disciplina
from core.get_db import get_db
from tqdm import tqdm
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DisciplinasTableBuilder(TableBuilder):

    def _build_impl(self, previous_result):
        curriculos = previous_result[1]
        disciplinas_raw = self.fetch_disciplinas(curriculos)
        formatted_disciplinas = self.process_data(disciplinas_raw)
        self.save_data(formatted_disciplinas)
        return formatted_disciplinas


    def fetch_disciplinas(self, curriculos):
        api = self.get_api_client()
        disciplinas_data = []    
        for curriculo in tqdm(curriculos, total=len(curriculos), desc="Fetching Disciplinas"):
            cod_curriculo = curriculo['codigo_curriculo']
            cod_curso = curriculo['codigo_curso']
            disciplinas_json = self._fetch_disciplinas(cod_curso, cod_curriculo, api)
            disciplinas_data.extend(disciplinas_json)
        return disciplinas_data
    
    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(min=5, max=120),
        retry=retry_if_exception_type(requests.exceptions.RequestException)
    )
    def _fetch_disciplinas(self, codigo_curso, codigo_curriculo, api):
        params = {
            'curso': codigo_curso,
            'curriculo': codigo_curriculo
        }
        response = api.request('/disciplinas-por-curriculo', params=params)
        if response.status_code != 200:
            logger.error(f"Erro ao buscar dados de disciplinas do curso {codigo_curso} e curriculo {codigo_curriculo}: {response.status_code}")
            if response.status_code == 500:
                raise requests.exceptions.RequestException(f"Erro ao buscar dados de disciplinas do curso {codigo_curso} e curriculo {codigo_curriculo}: {response.status_code}")
            return []
        disciplinas_json = response.json()
        if disciplinas_json is None:
            return []
        return disciplinas_json

        

    def get_api_client(self):
        api_client = APIClient(
            auth_url=settings.auth_url,
            base_url=settings.base_url,
            username=settings.username,
            password=settings.password
        )
        return api_client


    def process_data(self, disciplinas_raw):
        disciplina_mappings = load_column_mappings()['disciplinas']
        
        formatted_disciplinas = []
        for disciplina in tqdm(disciplinas_raw, total=len(disciplinas_raw), desc="Processing Disciplinas"):
            formatted_disciplina = rename_columns(disciplina, disciplina_mappings)
            formatted_disciplina = remove_extra_keys(formatted_disciplina, disciplina_mappings)
            formatted_disciplina['id'] = generate_disciplina_id(formatted_disciplina['codigo_curso'], formatted_disciplina['codigo_curriculo'], formatted_disciplina['codigo_disciplina'])
            formatted_disciplinas.append(formatted_disciplina)
        return formatted_disciplinas
    
    def save_data(self, disciplinas_data):
        with get_db() as db:
            try:
                db.bulk_insert_mappings(Disciplina, disciplinas_data)
                db.commit()
                logger.info("Dados de disciplinas salvos com sucesso")
            except:
                db.rollback()
                raise(Exception("Erro ao salvar dados de disciplinas no banco de dados"))