import logging
import requests
import time
from config.load_config import settings
from core.api import APIClient
from config.load_config import load_column_mappings
from .table_builder import TableBuilder
from core.utils import rename_columns, remove_extra_keys
from core.models.curriculo import Curriculo
from core.get_db import get_db
from tqdm import tqdm
from tenacity import retry, stop_after_attempt, retry_if_exception_type, wait_exponential
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CurriculosTableBuilder(TableBuilder):

    def _build_impl(self, cursos):
        curriculos_raw = self.fetch_curriculos(cursos)
        formatted_curriculos = self.process_data(curriculos_raw)
        self.save_data(formatted_curriculos)
        return formatted_curriculos

    def fetch_curriculos(self, cursos):
        api = self.get_api_client()
        curriculos_data = []
        for curso in tqdm(cursos, total=len(cursos), desc="Fetching Curriculos"):
            if curso['disponivel']:
                curriculos_json = self.fetch_curriculos_by_curso(curso['codigo_curso'], api)
                curriculos_data.extend(curriculos_json)
                time.sleep(1)
        return curriculos_data
    
    def get_api_client(self):
        api_client = APIClient(
            auth_url=settings.auth_url,
            base_url=settings.base_url,
            username=settings.username,
            password=settings.password
        )
        return api_client
    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(min=5, max=120),
        retry=retry_if_exception_type(requests.exceptions.RequestException)
    )
    def fetch_curriculos_by_curso(self, codigo_curso, api_client):
        params = {"curso": codigo_curso}
        response = api_client.request("/curriculos", params=params)
        if response.status_code != 200:
            logger.error(msg=f"Erro ao buscar curriculos do curso {codigo_curso}: {response.status_code}")
            if response.status_code == 500:
                raise(requests.exceptions.RequestException(f"Erro ao buscar curriculos do curso {codigo_curso}: {response.status_code}"))
        curriculos_json = response.json()
        if curriculos_json is None:
            logger.warning(msg=f"Curriculos do curso {codigo_curso} não encontrados")
            return []
        return curriculos_json
    
    def process_data(self, curriculos_raw):
        curriculo_mappings = load_column_mappings()['curriculos']
        formatted_curriculos = []
        for curriculo in tqdm(curriculos_raw, total=len(curriculos_raw), desc="Processing Curriculos"):
            formatted_curriculo = rename_columns(curriculo, curriculo_mappings)
            formatted_curriculo = remove_extra_keys(curriculo, curriculo_mappings)
            formatted_curriculos.append(formatted_curriculo)
        return formatted_curriculos
    
    def save_data(self, curriculos_data):
        with get_db() as db:
            try:
                db.bulk_insert_mappings(Curriculo, curriculos_data)
                db.commit()
                logger.info("Dados de curriculos salvos com sucesso")
            except:
                db.rollback()
                raise(Exception("Erro ao salvar dados de curriculos no banco de dados"))

            