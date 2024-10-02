# cursos-ufcg-data-bridge
Repositório dedicado ao sistema responsável por buscar e formatar dados para alimentar o banco de dados relacionado ao sistema de cursos da UFCG.

## Tecnologias Utilizadas
- Docker e Docker Compose
- Redis (para o backend do Celery e cache)
- MySQL (como banco de dados principal)
- Celery (para processamento assíncrono de tarefas)
- Python com SQLAlchemy e Pydantic

## Estrutura do Repositório
- app/: Contém o código-fonte principal da aplicação, incluindo as definições do Celery e a lógica de integração com APIs externas.
- core/: Contém a configuração de ambiente local e scripts principais para a execução do sistema.
- scripts/: Scripts auxiliares, incluindo o orchestrator que organiza a execução de tarefas.

## Pré-requisitos
- Docker e Docker Compose instalados na sua máquina.
- Python 3.9+ (caso queira executar localmente sem Docker)

## Configuração
### Arquivo .env
Certifique-se de criar um arquivo .env na raiz do projeto com as seguintes variáveis de ambiente para rodar o sistema no Docker:
    ```
    CELERY_BROKER_URL=redis://redis:6379/0
    CELERY_RESULT_BACKEND=redis://redis:6379/0
    ENVIRONMENT=development
    SOURCE_API_USERNAME=[username para o sistema Eureca]
    SOURCE_API_PASSWORD=[password para o sistema Eureca]
    DATABASE_URL="mysql+pymysql://root:${MYSQL_ROOT_PASSWORD}@db:3306/${MYSQL_DATABASE}"
    PYTHONPATH=/app
    MYSQL_ROOT_PASSWORD=[senha_do_user_do_db]
    MYSQL_DATABASE=[user_do_db]
    ```

Além disso, se você deseja executar localmente sem o Docker, crie um arquivo .env no diretório core com o seguinte conteúdo:
    ```
    CELERY_BROKER_URL=redis://localhost:6379/0
    CELERY_RESULT_BACKEND=redis://localhost:6379/0
    ENVIRONMENT=development
    SOURCE_API_USERNAME=[username para o sistema Eureca]
    SOURCE_API_PASSWORD=[password para o sistema Eureca]
    DATABASE_URL="mysql+pymysql://[user_do_db]:[senha_do_user]@localhost:3306/[esquema]"
    ```

## Como Rodar o Sistema

### Utilizando Docker Compose
1. Certifique-se de ter o Docker e Docker Compose instalados.
2. Execute o seguinte comando para subir os containers:
```
docker-compose up --build
```
Isso inicializará o Redis, MySQL, o Celery Worker e o Celery Beat. A aplicação será acessível dentro dos containers criados pelo Docker.

### Executando Localmente
Para rodar o sistema localmente (sem Docker), siga os passos abaixo:

1. Instale todas as dependências necessárias:
```
pip install -r requirements.txt

```
2. Após a instalação, execute o sistema utilizando o seguinte comando:
```
python -m scripts.orchestrator
```
Este comando iniciará o celery_worker e iniciará o orchestrador responsável por organizar a execução de tarefas do Celery.

## Estrutura do Docker Compose:
O arquivo docker-compose.yml está configurado da seguinte maneira:

- redis: Container que executa o Redis 6-alpine.
- db: Container que executa o MySQL 8.0 com um volume persistente para dados.
- celery_worker: Container que executa o worker Celery para processamento assíncrono.
- celery_beat: Container que executa o Celery Beat para agendar tarefas periódicas.
Os serviços são configurados para depender uns dos outros (Redis, MySQL) e são iniciados de acordo com as condições de saúde.

## Tarefas no Celery
- O Celery está configurado para processar múltiplas tarefas assíncronas usando Redis como broker e backend de resultados.
- As tarefas são organizadas e coordenadas através do script orchestrator.

## Considerações Finais
O sistema DataBridge UFCG é projetado para coletar e processar dados dos cursos da UFCG de maneira automatizada, com execução paralela de tarefas e persistência de dados.

## Como Rodar Todo o Sistema Cursos UFCG Usando Docker Compose
Para rodar o sistema completo do Cursos UFCG utilizando o arquivo docker-compose-cursos-ufcg.yml, siga os passos abaixo:
1. Pré-requisitos
- Docker e Docker Compose devem estar instalados no seu ambiente.
- Um arquivo .env na raiz do projeto com as seguintes variáveis de     ```
    CELERY_BROKER_URL=redis://redis:6379/0
    CELERY_RESULT_BACKEND=redis://redis:6379/0
    ENVIRONMENT=development
    SOURCE_API_USERNAME=[username para o sistema Eureca]
    SOURCE_API_PASSWORD=[password para o sistema Eureca]
    DATABASE_URL="mysql+pymysql://root:${MYSQL_ROOT_PASSWORD}@db:3306/${MYSQL_DATABASE}"
    PYTHONPATH=/app
    MYSQL_ROOT_PASSWORD=[senha_do_user_do_db]
    MYSQL_DATABASE=[user_do_db]
    ```
Este arquivo .env contém todas as variáveis de ambiente necessárias para a aplicação, como a configuração do Redis, MySQL e credenciais para o API.

2. Executar o Sistema
Com o Docker Compose configurado e o arquivo .env devidamente preenchido, siga estes passos:

1. Certifique-se de que o arquivo docker-compose-cursos-ufcg.yml está disponível no diretório do projeto.
2. Execute o seguinte comando para subir todos os containers e rodar o sistema:
```
docker-compose -f docker-compose-cursos-ufcg.yml up --build
```
Esse comando irá levantar todos os serviços necessários para o funcionamento completo do sistema, incluindo:

- Redis: Para cache e gerenciamento do Celery.
- MySQL: Para o banco de dados principal.
- Celery Worker: Para processamento assíncrono de tarefas.
- Celery Beat: Para agendamento de tarefas periódicas.
- Backend: A API para expor os dados processados.
- Frontend: A interface de usuário para visualização dos dados.

3. Acessando o Sistema
- Frontend: A interface pode ser acessada no navegador via http://localhost:3000.
- Backend: A API estará disponível em http://localhost:5000.
