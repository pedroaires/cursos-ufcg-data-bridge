import logging
import redis
import os
import subprocess
import time 
from redis import lock
from celery import chain, group, chord, shared_task
from config.db_config import reset_database, backup_database
from core.tasks import raise_table_simple, raise_table_with_result, app

logger = logging.getLogger(__name__)

redis_url = os.getenv("CELERY_BROKER_URL")
redis_client = redis.StrictRedis.from_url(redis_url)
LOCK_EXPIRE = 60 * 60 # Lock expira em 60 minutos


import redis
import logging

logger = logging.getLogger(__name__)

class RedisLock:
    def __init__(self, client, lock_name, expire=LOCK_EXPIRE):
        self.client = client
        self.lock_name = lock_name
        self.expire = expire

    def acquire(self):
        try:
            result = self.client.set(self.lock_name, 'locked', nx=True, px=self.expire * 1000)
            if result:
                logger.info(f"Lock {self.lock_name} acquired")
            else:
                logger.info(f"Lock {self.lock_name} already held by another process")
            return result
        except redis.RedisError as e:
            logger.error(f"Error acquiring lock: {e}")
            return False

    def release(self):
        try:
            # Release the lock by deleting the key
            result = self.client.delete(self.lock_name)
            if result:
                logger.info(f"Lock {self.lock_name} released")
            else:
                logger.warning(f"Lock {self.lock_name} was not held")
            return result
        except redis.RedisError as e:
            logger.error(f"Error releasing lock: {e}")
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
        group(
            raise_table_with_result.s("Disciplinas"),
            raise_table_with_result.s("Historico")
        ),
        raise_table_with_result.s("Prerequisitos"),
        finish_batched_workflow.s(),
    )
    return workflow

    

def batch_data(data, batch_size=10):
    for i in range(0, len(data), batch_size):
        yield data[i:i+batch_size]

@shared_task(ignore_result=True)
def finish_task(prev_task_result=None):
    lock_name = "orchestrate_tasks_lock"
    RedisLock(redis_client, lock_name).release()
    logger.info(msg="Workflow finalizado!")

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
    worker = subprocess.Popen(['celery', '-A', 'core.tasks', 'worker', '--loglevel=info', '-n', 'worker_from_script', '--concurrency=2'])
    time.sleep(5)
    app.send_task('scripts.orchestrator.orchestrate_tasks')
    time.sleep(5)
    lock_name = "orchestrate_tasks_lock"
    lock = RedisLock(redis_client, lock_name)

    while not lock.acquire():
        time.sleep(3*60)
    logger.info("Finalizando o worker...")
    lock.release()
    worker.terminate()
