from celery import chain, group
from core.tasks.cursos_tasks import fetch_cursos, process_data as process_curso_data, save_data as save_curso_data
from core.tasks.alunos_tasks import fetch_alunos, process_data as process_aluno_data, save_data as save_aluno_data
from core.tasks.curriculos_tasks import fetch_curriculos, process_data as process_curriculo_data, save_data as save_curriculo_data

import logging

logger = logging.getLogger(__name__)
def save_all_data():
    print("Salvando todos os dados...")
    save_curso_data.delay()
    save_aluno_data.delay()
    save_curriculo_data.delay()
    print("Dados salvos com sucesso!")

def orchestrate_tasks():
    print("Orquestrando tarefas...")	
    workflow = chain(
        fetch_cursos.s(),
        process_curso_data.s(),

        fetch_alunos.s(),
        fetch_curriculos.s(),
        
        process_aluno_data.s(),
        process_curriculo_data.s()
        
    )
    print("Iniciando workflow...")
    result = workflow.apply_async()
    print("Workflow iniciado!")
    result.get() # Wait for the workflow to finish
    print("Workflow finalizado!")

    print("Salvando todos os dados...")
    save_all_data()
    print("Todas as tarefas foram executadas com sucesso!")
    

# def orchestrate_tasks():
#     print("Orquestrando tarefas...")	
    
#     fetch_cursos.delay()
#     process_curso_data.delay()

#     fetch_alunos.delay()
#     fetch_curriculos.delay()
    
#     process_aluno_data.delay()
#     process_curriculo_data.delay()
    
#     print("Workflow finalizado!")

#     print("Salvando todos os dados...")
#     save_all_data()
#     print("Todas as tarefas foram executadas com sucesso!")


if __name__ == '__main__':
    orchestrate_tasks()