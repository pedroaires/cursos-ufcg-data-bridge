import logging

from config.load_config import settings
from core.api import APIClient
from config.load_config import load_column_mappings
from .table_builder import TableBuilder
from core.utils import rename_columns, remove_extra_keys
from core.models.aluno import Aluno
from core.get_db import get_db
from tqdm import tqdm

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AlunosTableBuilder(TableBuilder):

    def _build_impl(self, cursos):
        alunos_raw = self.fetch_alunos(cursos)
        formatted_alunos = self.process_data(alunos_raw)
        self.save_data(formatted_alunos)
        return formatted_alunos

    
    def fetch_alunos(self, cursos):
        api = self.get_api_client()
        alunos_data = []
        for curso in tqdm(cursos, total=len(cursos), desc="Fetching Alunos"):
            if curso['disponivel']:
                alunos_do_curso = self.fetch_alunos_by_curso(curso['codigo_curso'], api)
                alunos_data.extend(alunos_do_curso)
        return alunos_data
    
    def fetch_alunos_by_curso(self, codigo_curso, api_client):
        params = {
            'curso': codigo_curso
        }
        response = api_client.request('/estudantes', params=params)
        if response.status_code != 200:
            logger.error(f"Erro ao buscar dados de alunos do curso {codigo_curso}: {response.status_code}")
            
            return []
        alunos_json = response.json()
        if alunos_json is None:
            return []
        return alunos_json
    
    def get_api_client(self):
        api_client = APIClient(
            auth_url=settings.auth_url,
            base_url=settings.base_url,
            username=settings.username,
            password=settings.password
        )
        return api_client
    
    def process_data(self, alunos_data):
        aluno_mappings = load_column_mappings()['alunos']
        
        formatted_alunos = []
        for aluno in tqdm(alunos_data, total=len(alunos_data), desc="Processing Alunos"):
            formatted_aluno = rename_columns(aluno, aluno_mappings)
            formatted_aluno = remove_extra_keys(formatted_aluno, aluno_mappings)
            formatted_alunos.append(formatted_aluno)
        
        return formatted_alunos
        
    def save_data(self, alunos_data):
        with get_db() as db:
            try:
                db.bulk_insert_mappings(Aluno, alunos_data)
                db.commit()
                logger.info("Dados de alunos salvos com sucesso!")
            except:
                db.rollback()
                raise(Exception("Erro ao salvar dados de alunos no banco de dados"))