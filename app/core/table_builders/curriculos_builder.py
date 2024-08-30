import logging

from config.load_config import settings
from core.api import APIClient
from config.load_config import load_column_mappings
from .table_builder import TableBuilder
from core.utils import rename_columns, remove_extra_keys
from core.models.curriculo import Curriculo
from core.get_db import get_db
from tqdm import tqdm

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
        for curso in tqdm(cursos[:10], total=len(cursos[:10])):
            if curso['disponivel']:
                curriculos_json = self.fetch_curriculos_list(curso['codigo_curso'], api)
                for curr_dict in curriculos_json:
                    cod_curriculo = curr_dict['curriculumCode']
                    curriculo_info_json = self.fetch_curriculos_info(curso['codigo_curso'], cod_curriculo, api)
                    curriculo_info_json['codigo_curso'] = curso['codigo_curso']
                    curriculo_info_json['codigo_curriculo'] = cod_curriculo
                    curriculos_data.append(curriculo_info_json)
        return curriculos_data
    
    def get_api_client(self):
        api_client = APIClient(
            auth_url=settings.auth_url,
            base_url=settings.base_url,
            username=settings.username,
            password=settings.password
        )
        return api_client

    def fetch_curriculos_list(self, codigo_curso, api_client):
        params = {"courseCode": codigo_curso}
        curriculos_json = api_client.request("/course/getActivesCurriculum", params=params)
        if 'errors' in curriculos_json:
            print("Rota nao retornou o curriculo corretamente, tentando outra rota...")
            curriculos_json = api_client.request("/course/getCurriculumCodes", params=params)
        return curriculos_json

    def fetch_curriculos_info(self, codigo_curso, codigo_curriculo, api_client):
        params = {"courseCode": codigo_curso, "curriculumCode": codigo_curriculo}
        curriculo_info_json = api_client.request("/course/getCurriculum", params=params)
        return curriculo_info_json
    
    def process_data(self, curriculos_raw):
        curriculo_mappings = load_column_mappings()['curriculos']
        formatted_curriculos = []
        for curriculo in curriculos_raw:
            formatted_curriculo = rename_columns(curriculo, curriculo_mappings)
            formatted_curriculo = remove_extra_keys(curriculo, curriculo_mappings)
            formatted_curriculos.append(formatted_curriculo)
        return formatted_curriculos
    
    def save_data(self, curriculos_data):
        with get_db() as db:
            try:
                db.bulk_insert_mappings(Curriculo, curriculos_data)
                db.commit()
            except:
                db.rollback()
                raise(Exception("Erro ao salvar dados de curriculos no banco de dados"))

            