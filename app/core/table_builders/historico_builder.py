import logging

from config.load_config import settings
from core.api import APIClient
from config.load_config import load_column_mappings
from .table_builder import TableBuilder
from core.utils import rename_columns, remove_extra_keys, generate_disciplina_id
from core.models.historico import Historico
from core.get_db import get_db
from tqdm import tqdm
import time
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HistoricoTableBuilder(TableBuilder):

    def _build_impl(self, previous_result):
        alunos = previous_result[0]
        historico_raw = self.fetch_historico(alunos)
        formatted_historico = self.process_data(historico_raw)
        self.save_data(formatted_historico)

    def get_api_client(self):
        api_client = APIClient(
            auth_url=settings.auth_url,
            base_url=settings.base_url,
            username=settings.username,
            password=settings.password
        )
        return api_client
    
    def fetch_historico(self, alunos):
        api = self.get_api_client()
        historico_data = []
        for aluno in tqdm(alunos, total=len(alunos), desc="Fetching historico"):
            aluno_json = self._fetch_historico(aluno['matricula'], api)
            if aluno_json != []:
                historicos_json = self._get_historicos_from_aluno(aluno_json)
                historico_data.extend(historicos_json)
        return historico_data
    
    def _get_historicos_from_aluno(self, aluno):
        mappings = load_column_mappings()['historico']
        reverse_mappings = {v:k for k,v in mappings.items()}
        try:
            historicos = aluno.pop('historico_de_matriculas')
        except Exception as e:
            logger.error(f"Erro ao buscar dados de historico do aluno {aluno}: {e}")
            return []
        historico_data = []
        for historico in historicos:
            historico_dict = {
                'codigo_curriculo': aluno[reverse_mappings['codigo_curriculo']],
                'codigo_curso': aluno[reverse_mappings['codigo_curso']],
                'matricula': aluno[reverse_mappings['matricula']],
            }
            extra_info = {k: historico[k] for k in mappings.keys() if k in historico}
            historico_dict.update(extra_info)
            historico_data.append(historico_dict)
        return historico_data
        
            

    def _fetch_historico(self, matricula, api):
        params = {
            'estudante': matricula
        }
        response = api.request('/estudantes/historico/estudante-anonimizado', params=params)
        if response.status_code != 200:
            logger.error(f"Erro ao buscar dados de historico do aluno {matricula} na API: {response.status_code}")
            return []
        historicos_json = response.json()
        if historicos_json is None:
            return []
        return historicos_json
    
    def process_data(self, historicos_raw):
        historico_mappings = load_column_mappings()['historico']
        formatted_historicos = []
        for historico in tqdm(historicos_raw, total=len(historicos_raw), desc="Processing Historico"):
            formatted_historico = rename_columns(historico, historico_mappings)
            formatted_historico = remove_extra_keys(formatted_historico, historico_mappings)
            formatted_historicos.append(formatted_historico)
        return formatted_historicos


    def save_data(self, historico_data):
        with get_db() as db:
            try:
                db.bulk_insert_mappings(Historico, historico_data)
                db.commit()
                logger.info("Dados de historico salvos com sucesso")
            except:
                db.rollback()
                raise(Exception("Erro ao salvar dados de historico no banco de dados"))