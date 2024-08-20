from celery import chain, group
from config.db_config import reset_database
import core.tasks.cursos_tasks as cursos
import core.tasks.curriculos_tasks as curriculos
import core.tasks.alunos_tasks as alunos

import logging

logger = logging.getLogger(__name__)
def save_all_data():
    print("Salvando todos os dados...")
    cursos.save_data.delay()
    alunos.save_data.delay()
    curriculos.save_data.delay()
    print("Dados salvos com sucesso!")

def orchestrate_tasks():
    print("Orquestrando tarefas...")	
    print("Resetando BD...")
    reset_database()
    print("BD resetado!")

    workflow = chain(
        cursos.fetch_cursos.s(),
        cursos.process_data.s(),

        alunos.fetch_alunos.s(),
        curriculos.fetch_curriculos.s(),
        
        alunos.process_data.s(),
        curriculos.process_data.s(),
        
        cursos.save_data.s(),
        alunos.save_data.s(),
        curriculos.save_data.s()
        
    )
    print("Iniciando workflow...")
    result = workflow.apply_async()
    print("Workflow iniciado!")
    result.get() # Wait for the workflow to finish
    print("Workflow finalizado!")

    # print("Salvando todos os dados...")
    # save_all_data()
    # print("Todas as tarefas foram executadas com sucesso!")


if __name__ == '__main__':
    orchestrate_tasks()