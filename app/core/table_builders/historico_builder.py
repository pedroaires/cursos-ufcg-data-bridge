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

    def _build_impl(self, disciplinas):
        historico_raw = self.fetch_historico(disciplinas)
        formatted_historico = self.process_data(historico_raw)
        self.save_data(formatted_historico, disciplinas)
        return formatted_historico

    def get_api_client(self):
        api_client = APIClient(
            auth_url=settings.auth_url,
            base_url=settings.base_url,
            username=settings.username,
            password=settings.password
        )
        return api_client
    def _get_curso_curriculos_unique(self, disciplinas):
        start = time.time()
        unique_combinations = set()
        for disciplina in disciplinas:
            codigo_curso = disciplina['codigo_curso']
            codigo_curriculo = disciplina['codigo_curriculo']
            unique_combinations.add((codigo_curso,  codigo_curriculo))
        end = time.time()
        print(f"Took {end - start} to generate curso and curriculo combinations")
        return [{'codigo_curso': cod_curso, 'codigo_curriculo': cod_curr} for cod_curso, cod_curr in unique_combinations]
    
    def fetch_historico(self, disciplinas):
        api = self.get_api_client()
        curriculos = self._get_curso_curriculos_unique(disciplinas)
        historico_data = []
        for curriculo in tqdm(curriculos, total=len(curriculos), desc="Fetching historico"):
            cod_curriculo = curriculo['codigo_curriculo']
            cod_curso = curriculo['codigo_curso']
            historicos_json = self._fetch_historico(cod_curso, cod_curriculo, api)
            historico_data.extend([{**historico, 'codigo_curriculo': cod_curriculo, 'codigo_curso': cod_curso} for historico in historicos_json])
        return historico_data
    
    def _fetch_historico(self, codigo_curso, codigo_curriculo, api):
        params = {
            'curriculumCode': codigo_curriculo,
            'courseCode': codigo_curso,
            'from': '0000.0',
            'to': '9999.9',
            'anonymize': 'true'
        }
        historicos_json = api.request('/enrollments', params=params)
        return historicos_json
    
    def process_data(self, historicos_raw):
        historico_mappings = load_column_mappings()['historico']
        
        formatted_historicos = []
        for historico in tqdm(historicos_raw, total=len(historicos_raw), desc="Processing Historico"):
            formatted_historico = rename_columns(historico, historico_mappings)
            formatted_historico = remove_extra_keys(formatted_historico, historico_mappings)
            formatted_historicos.append(formatted_historico)
        return formatted_historicos
    
    def _build_disc_lookup(self, disciplinas_data):
        disciplinas_lookup = {
                disc["id"]: disc
            for disc in disciplinas_data
        }
        return disciplinas_lookup

    def validate_historico_data(self, historico_data, disciplinas):
        disc_lookup = self._build_disc_lookup(disciplinas)
        valid_historico_data = []
        invalid_historico_data = []
        
        for historico in tqdm(historico_data, total=len(historico_data), desc="Validating Hisotrico Data"):
            cod_disc = historico['codigo_disciplina']
            cod_curr = historico['codigo_curriculo']
            cod_curso = historico['codigo_curso']
            disc_id = generate_disciplina_id(cod_curso, cod_curr, cod_disc)
            if disc_id in disc_lookup:
                valid_historico_data.append(historico)
            else:
                invalid_historico_data.append(historico)
        
        return valid_historico_data, invalid_historico_data
        


    def insert_valid_data(self, db, valid_historico_data):
        try:
            db.bulk_insert_mappings(Historico, valid_historico_data)
            db.commit()
            print(f"{len(valid_historico_data)} registros inseridos com sucesso.")
        except Exception as e:
            db.rollback()
            print(f"Erro ao inserir dados: {e}")
            raise e


    def log_invalid_data(self, invalid_historico_data):
        if invalid_historico_data:
            print(f"Dados inválidos: {invalid_historico_data[:10]}")


    def save_data(self, historico_data, disciplinas):
        with get_db() as db:
            valid_historico_data, invalid_historico_data = self.validate_historico_data(historico_data, disciplinas)
            
            if valid_historico_data:
                self.insert_valid_data(db, valid_historico_data)
            
            self.log_invalid_data(invalid_historico_data)