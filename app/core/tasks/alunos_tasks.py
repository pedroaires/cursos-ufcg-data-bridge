from core.celery_app import app
from core.api import APIClient
from core.config import settings

api_client = APIClient(
    auth_url=settings.auth_url,
    base_url=settings.base_url,
    username=settings.username,
    password=settings.password
)

@app.task
def fetch_alunos(previous_task_result=None):
    print("Buscando dados de ALUNOS...")
    return "Dados de ALUNOS buscados com sucesso!"

@app.task
def process_data(previous_task_result=None):
    print("Processando dados de ALUNOS...")

@app.task
def save_data(previous_task_result=None):
    print("Salvando dados de ALUNOS...")