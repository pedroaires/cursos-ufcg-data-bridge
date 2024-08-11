from core.tasks.cursos_tasks import app as curso_app

if __name__ == '__main__':
    curso_app.worker_main(argv=['worker', '--loglevel=info'])