from core.celery_app import app
from core.api import APIClient
from core.config import settings
from core.redis_cache import RedisCache

api_client = APIClient(
    auth_url=settings.auth_url,
    base_url=settings.base_url,
    username=settings.username,
    password=settings.password
)

redis_cache = RedisCache()

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
    redis_cache.set_data("cursos", {'codigo_curso': [1,2,3,4], 'curso': ['a, b', 'c', 'd']}, expire=60)
    print("Dados processados e colocados no REDIS!")

@app.task
def save_data(previous_task_result=None):
    print("Salvando dados...")
