from celery import Celery
from core.api import APIClient
from core.config import settings

app = Celery('tasks')
app.config_from_object('celery_config')

api_client = APIClient(
    auth_url=settings.auth_url,
    base_url=settings.base_url,
    username=settings.username,
    password=settings.password
)

@app.task
def fetch_curriculos():
    print("Buscando dados de CURRICULOS...")

@app.task
def process_data():
    print("Processando dados de CURRICULOS...")

@app.task
def save_data():
    print("Salvando dados de CURRICULOS...")