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
def fetch_curriculos(previous_task_result=None):
    print("Buscando dados de CURRICULOS...")

@app.task
def process_data(previous_task_result=None):
    print("Processando dados de CURRICULOS...")

@app.task
def save_data(previous_task_result=None):
    print("Salvando dados de CURRICULOS...")