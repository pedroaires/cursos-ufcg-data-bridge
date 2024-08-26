from celery import chain, group
from config.db_config import reset_database
import core.tasks.cursos_tasks as cursos
import core.tasks.curriculos_tasks as curriculos
import core.tasks.alunos_tasks as alunos
import core.tasks.disciplinas_tasks as disciplinas
import core.tasks.historico_tasks as historico
import logging

logger = logging.getLogger(__name__)

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
        
        disciplinas.fetch_disciplinas.s(),
        disciplinas.process_data.s(),
        historico.fetch_historicos.s(),
        historico.process_data.s(),

        cursos.save_data.s(),
        alunos.save_data.s(),
        curriculos.save_data.s(),
        disciplinas.save_data.s(),
        historico.save_data.s()
        
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