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
        raise_table_with_result.s("Historico"),
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
    result.get() # Wait for the workflow to finish
    print("Workflow finalizado!")

    # print("Salvando todos os dados...")
    # save_all_data()
    # print("Todas as tarefas foram executadas com sucesso!")

if __name__ == '__main__':
    orchestrate_tasks()