from celery import Celery
from core.api import APIClient
from core.config import settings
from celery.signals import worker_ready

app = Celery('tasks')
app.config_from_object('celery_config')

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
def process_data():
    print("Processando dados...")

@app.task
def save_data():
    print("Salvando dados...")


# @worker_ready.connect
# def at_start(sender, **kwargs):
#     run_