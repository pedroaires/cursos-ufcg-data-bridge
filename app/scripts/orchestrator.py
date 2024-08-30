from celery import chain, group
from config.db_config import reset_database
from core.table_tasks import raise_table_simple, raise_table_with_result
import logging

logger = logging.getLogger(__name__)

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
    )
    return workflow

def orchestrate_tasks():
    print("Orquestrando tarefas...")	
    print("Resetando BD...")
    reset_database()
    print("BD resetado!")

    print("Iniciando workflow...")
    workflow = build_workflow()
    result = workflow.apply_async()
    print("Workflow iniciado!")
    result.get() 
    print("Workflow finalizado!")
if __name__ == '__main__':
    orchestrate_tasks()