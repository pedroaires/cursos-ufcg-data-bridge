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
def fetch_cursos():
    print("Buscando cursos...")
    print("API Client:")
    print(f"Auth URL: {api_client.auth_url}")
    print(f"Base URL: {api_client.base_url}")
    print(f"Username: {api_client.username}")
    print(f"Password: {api_client.password}")

@app.task
def process_data(previous_task_result=None):
    print("Processando dados...")

@app.task
def save_data(previous_task_result=None):
    print("Salvando dados...")
