import logging
import time
import redis

from celery import chain, group, shared_task
from config.db_config import reset_database
from core.tasks import raise_table_simple, raise_table_with_result

logger = logging.getLogger(__name__)

redis_client = redis.StrictRedis(host='localhost', port=6379, db=0)
LOCK_EXPIRE = 60 * 30 # Lock expires in 30 minutes


class RedisLock:
    def __init__(self, client, lock_name, expire=LOCK_EXPIRE):
        self.client = client
        self.lock_name = lock_name
        self.expire = expire

    def acquire(self):
        return self.client.set(self.lock_name, 'true', ex=self.expire, nx=True)

    def release(self):
        return self.client.delete(self.lock_name)
    

def build_workflow():
    workflow = chain(
        raise_table_simple.s("Cursos"),
        group(
            raise_table_with_result.s("Alunos"),
            raise_table_with_result.s("Curriculos"),
        ),
        raise_table_with_result.s("Disciplinas"),
        group(
            raise_table_with_result.s("Historico"),
            raise_table_with_result.s("Prerequisitos"),
        ),
        finish_task.s()
    )
    return workflow

@shared_task
def finish_task(prev_task_result=None):
    lock_name = "orchestrate_tasks_lock"
    RedisLock(redis_client, lock_name).release()
    print("Workflow finalizado!")

@shared_task
def orchestrate_tasks():
    lock_name = "orchestrate_tasks_lock"
    lock = RedisLock(redis_client, lock_name)
    if lock.acquire():
        try:
            logger.info(msg="Lock acquired for orchestrate_tasks")
            logger.info(msg="Orquestrando tarefas...")	
            logger.info(msg="Resetando BD...")
            reset_database()
            logger.info(msg="BD resetado!")

            logger.info(msg="Iniciando workflow...")
            workflow = build_workflow()
            workflow.apply_async()
        except Exception as e:
            logger.error(f"Error in orchestrate_tasks: {e}")
            lock.release()
    else:
        logger.info("Lock not acquired for orchestrate_tasks")
        return None

if __name__ == '__main__':
    result = orchestrate_tasks().apply()
    result.get()