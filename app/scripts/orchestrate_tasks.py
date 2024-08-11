from celery import chain, group
from core.tasks.cursos_tasks import fetch_cursos, process_data as process_curso_data, save_data as save_curso_data
from core.tasks.alunos_tasks import fetch_alunos, process_data as process_aluno_data, save_data as save_aluno_data
from core.tasks.curriculos_tasks import fetch_curriculos, process_data as process_curriculo_data, save_data as save_curriculo_data

def save_all_data():
    print("Salvando todos os dados...")
    save_curso_data().delay()
    save_aluno_data().delay()
    save_curriculo_data().delay()
    print("Dados salvos com sucesso!")

def orchestrate_tasks():
    workflow = chain(
        fetch_cursos.s(),
        process_curso_data.s(),
        group(
            fetch_alunos.s(),
            fetch_curriculos.s()
            ),
        group(
            process_aluno_data.s(),
            process_curriculo_data.s()
        )

    )
    result = workflow.apply_async()
    result.get() # Wait for the workflow to finish

    save_all_data()
    
if __name__ == '__main__':
    orchestrate_tasks()