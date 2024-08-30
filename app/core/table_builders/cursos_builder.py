import pandas as pd
import re
import unidecode

from config.load_config import settings
from core.api import APIClient
from config.load_config import load_column_mappings
from .table_builder import TableBuilder
from core.utils import rename_columns, remove_extra_keys
from core.models.curso import Curso
from core.get_db import get_db


class CursosTableBuilder(TableBuilder):

    def _build_impl(self, previous_task_result=None):
        cursos_raw = self.fetch_cursos()
        formatted_cursos = self.processa_cursos(cursos_raw)
        self.save_data(formatted_cursos)
        return formatted_cursos
    
    def fetch_cursos(self):
        api = self.get_api_client()
        cursos = api.request("/courses/getActives")
        if 'errors' in cursos:
            raise Exception("Ocorreu um erro ao buscar os cursos")
        return cursos
    
    def processa_cursos(self, cursos):
        campus_info = pd.read_csv('./data/campus_info.csv')
        formatted_data = self.formata_fields_campos(cursos, campus_info)
        return formatted_data
    
    def formata_fields_campos(self, cursos, campus_info):
        formatted_cursos = []
        curso_mappings = load_column_mappings()['cursos']
        for curso in cursos:
            campus_abrev = self.get_campus_abrev(curso['code'], campus_info)
            nome_schema = self.formata_schema_curso(curso['name'], campus_abrev)
            formatted_curso = {k:v for k,v in curso.items()}
            formatted_curso['campus'] = campus_abrev
            formatted_curso['schema'] = nome_schema
            formatted_curso['disponivel'] = curso['status'] == 'A'
            formatted_curso = rename_columns(formatted_curso, curso_mappings)
            formatted_curso = remove_extra_keys(formatted_curso, curso_mappings)
            formatted_cursos.append(formatted_curso)
        
        return formatted_cursos

    def get_campus_abrev(self, course_code, campus_info_df):
        campus_abrev = campus_info_df.loc[campus_info_df['codigo_campus'] == int(course_code[0]), 'campus_abreviado']
        if not campus_abrev.empty:
            return campus_abrev.iloc[0]
        return ''    
    
    def formata_schema_curso(self, nome_curso, campus_abrev):
        nome_normalizado = unidecode.unidecode(nome_curso).lower()
        nome_formatado = re.sub('[^a-z]+|(?!_)$', '_', nome_normalizado)
        return nome_formatado + campus_abrev.lower()
        
    def get_api_client(self):
        api_client = APIClient(
            auth_url=settings.auth_url,
            base_url=settings.base_url,
            username=settings.username,
            password=settings.password
        )
        return api_client

    def save_data(self, cursos):
        with get_db() as db:
            try:
                db.bulk_insert_mappings(Curso, cursos)
                db.commit()
            except:
                db.rollback()
                raise(Exception("Erro ao salvar dados de cursos no banco de dados"))