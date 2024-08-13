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
def fetch_alunos(previous_task_result=None):
    cursos = redis_cache.get_data("cursos")
    print("Cursos:")
    print(cursos)
    print("Buscando dados de ALUNOS...")
    return "Dados de ALUNOS buscados com sucesso!"

@app.task
def process_data(previous_task_result=None):
    print("Processando dados de ALUNOS...")

@app.task
def save_data(previous_task_result=None):
    print("Salvando dados de ALUNOS...")