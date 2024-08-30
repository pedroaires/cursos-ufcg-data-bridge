import logging
import time
import json

from config.load_config import settings
from core.api import APIClient
from config.load_config import load_column_mappings
from .table_builder import TableBuilder
from core.utils import rename_columns, remove_extra_keys, generate_disciplina_id
from core.models.disciplina import prerequisitos
from core.get_db import get_db
from sqlalchemy import insert
from tqdm import tqdm

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PrerequisitosTableBuilder(TableBuilder):

    def _build_impl(self, disciplinas):
        prerequisitos_raw = self.fetch_prerequisitos()
        formatted_prerequisitos = self.process_data(prerequisitos_raw)
        self.save_data(formatted_prerequisitos, disciplinas)
        return formatted_prerequisitos

    def fetch_prerequisitos(self):
        with open("data/PRE_REQUISITOS_DISCIPLINA.json") as f:
            prereqs_data = json.load(f)
        return prereqs_data
    
    def process_data(self, prerequisitos_raw):
        prerequisito_mappings = load_column_mappings()['prerequisitos']
        formatted_prerequisitos = []
        for prereq in tqdm(prerequisitos_raw, total=len(prerequisitos_raw), desc="Processing Prerequisitos"):
            formatted_prerequisito = rename_columns(prereq, prerequisito_mappings)
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
        mapped_prereq = set()

        for prereq in tqdm(prereq_data, total=len(prereq_data), desc="Validating Prerequisitos Data"):
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
            else:
                print("Nenhum dado válido encontrado.")
            self.log_invalid_data(invalid_prereqs)