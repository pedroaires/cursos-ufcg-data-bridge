import logging
import redis
import os
import subprocess
import time 
from celery import chain, group, chord, shared_task
from config.db_config import reset_database, backup_database
from core.tasks import raise_table_simple, raise_table_with_result, app

logger = logging.getLogger(__name__)

redis_url = os.getenv("CELERY_BROKER_URL")
redis_client = redis.StrictRedis.from_url(redis_url)
LOCK_EXPIRE = 60 * 30 # Lock expira em 30 minutos


class RedisLock:
    def __init__(self, client, lock_name, expire=LOCK_EXPIRE):
        self.client = client
        self.lock_name = lock_name
        self.expire = expire

    def acquire(self):
        try:
            return self.client.set(self.lock_name, 'true', ex=self.expire, nx=True)
        except redis.RedisError as e:
            logger.error(f"Error ao adiquirir a lock: {e}")
            return False
    def release(self):
        try:
            return self.client.delete(self.lock_name)
        except redis.RedisError as e:
            logger.error(f"Erro ao liberar lock: {e}")
            return False
    

@shared_task(ignore_result=True)
def finish_batched_workflow(prev_task_result=None):
    logger.info("Todos os Batches finalizados!")

def build_batches(cursos_data, batch_size=10):
    batch_workflows = []
    for batch in batch_data(cursos_data, batch_size):
        batch_workflow = batched_workflow(batch)
        batch_workflows.append(batch_workflow)
    return batch_workflows

    
def batched_workflow(cursos_data):
    workflow = chain(
        group(
            raise_table_with_result.si(cursos_data, "Alunos"),
            raise_table_with_result.si(cursos_data, "Curriculos"),
        ),
        raise_table_with_result.s("Disciplinas"),
        group(
            raise_table_with_result.s("Historico"),
            raise_table_with_result.s("Prerequisitos"),
        )
    )
    return workflow

    

def batch_data(data, batch_size=10):
    for i in range(0, len(data), batch_size):
        yield data[i:i+batch_size]

@shared_task(ignore_result=True)
def finish_task(prev_task_result=None):
    lock_name = "orchestrate_tasks_lock"
    RedisLock(redis_client, lock_name).release()
    print("Workflow finalizado!")

@shared_task(ignore_result=True)
def orchestrate_tasks():
    lock_name = "orchestrate_tasks_lock"
    lock = RedisLock(redis_client, lock_name)
    if lock.acquire():
        try:
            logger.info(msg="Lock adquirida")
            
            logger.info(msg='Iniciando backup do BD')
            backup_success = backup_database()
            logger.info(msg='Backup finalizado')
            if not backup_success:
                logger.error(msg="Backup falhou, abortando workflow...")
                lock.release()
                return None
            logger.info(msg="Resetando BD...")
            reset_database()
            logger.info(msg="BD resetado!")

            logger.info(msg="Iniciando workflow...")
            cursos_data = raise_table_simple("Cursos")
            batch_workflows = build_batches(cursos_data)
            chord(batch_workflows)(finish_task.s())
            logger.info(msg="Workflow iniciado!")
        except Exception as e:
            logger.error(f"Erro em orchestrate_tasks: {e}")
            lock.release()
    else:
        logger.info("Lock nao adquirida para orchestrate tasks")
        return None

if __name__ == '__main__':
    # worker = subprocess.Popen(['celery', '-A', 'core.tasks', 'worker', '--loglevel=info', '-n', 'worker_from_script', '--concurrency=1', '--max-tasks-per-child=1'])
    # time.sleep(5)
    # result = app.send_task('scripts.orchestrator.orchestrate_tasks')
    # inspector = app.control.inspect()
    
    # while True:
    #     active_tasks = inspector.active()
        
    #     # Check if there are any active tasks
    #     if len(active_tasks.items()) > 0:
    #         logger.info(f"Tasks ativas: {active_tasks}")
    #         time.sleep(30)
    #     else:
    #         logger.info("Tarefas finalizadas")
    #         worker.terminate()
    app.send_task('scripts.orchestrator.orchestrate_tasks')