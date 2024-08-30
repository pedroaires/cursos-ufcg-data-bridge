import logging

from config.load_config import settings
from core.api import APIClient
from config.load_config import load_column_mappings
from .table_builder import TableBuilder
from core.utils import rename_columns, remove_extra_keys
from core.models.aluno import Aluno
from core.get_db import get_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AlunosTableBuilder(TableBuilder):

    def _build_impl(self, cursos):
        logger.info("Começando o processo de subida de alunos")
        alunos_raw = self.fetch_alunos(cursos)
        formatted_alunos = self.process_data(alunos_raw)
        self.save_data(formatted_alunos)
        logger.info("Finalizando subida da tabela de alunos")
        return formatted_alunos

    
    def fetch_alunos(self, cursos):
        if not cursos:
            raise Exception("Dados de cursos não podem ser nulos para criação da tabela de alunos")
        
        api = self.get_api_client()
        alunos_data = []
        for curso in cursos[:10]:
            if curso['disponivel']:
                alunos_do_curso = self.fetch_alunos_by_curso(curso['codigo_curso'], api)
                alunos_data.extend(alunos_do_curso)
        return alunos_data
    
    def fetch_alunos_by_curso(self, codigo_curso, api_client):
        params = {
            'courseCode': codigo_curso,
            'from': '0000.0',
            'to': '9999.9',
            'anonymize': 'true'
        }
        alunos_json = api_client.request('/students', params=params)
        alunos_do_curso = []
        if 'students' in alunos_json:
            for aluno in alunos_json['students']:
                aluno['codigo_curso'] = codigo_curso
                alunos_do_curso.append(aluno)
        else:
            raise(f"Error on course {codigo_curso}")
        return alunos_do_curso
    
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
        for aluno in alunos_data:
            formatted_aluno = rename_columns(aluno, aluno_mappings)
            formatted_aluno = remove_extra_keys(formatted_aluno, aluno_mappings)
            formatted_alunos.append(formatted_aluno)
        
        return alunos_data
        
    def save_data(self, alunos_data):
        with get_db() as db:
            try:
                db.bulk_insert_mappings(Aluno, alunos_data)
                db.commit()
            except:
                db.rollback()
                raise(Exception("Erro ao salvar dados de alunos no banco de dados"))