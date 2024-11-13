# cursos-ufcg-data-bridge
Repositório dedicado ao sistema responsável por buscar e formatar dados para alimentar o banco de dados relacionado ao sistema de cursos da UFCG.

## Tecnologias Utilizadas
- Docker e Docker Compose
- Redis (para o backend do Celery e cache)
- MySQL (como banco de dados principal)
- Celery (para processamento assíncrono de tarefas)
- Python com SQLAlchemy

## Estrutura do Repositório
- app/: Contém o código-fonte principal da aplicação, incluindo as definições do Celery e a lógica de integração com APIs externas.
- core/: Contém a configuração de ambiente local e scripts principais para a execução do sistema.
- scripts/: Scripts auxiliares, incluindo o orchestrator que organiza a execução das tarefas de levantar as tabelas.

## Pré-requisitos
- Docker e Docker Compose instalados na sua máquina.

## Configuração
### Arquivo .env
Certifique-se de criar um arquivo .env na raiz do projeto com as seguintes variáveis de ambiente para rodar o sistema no Docker:

```
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
ENVIRONMENT=production
SOURCE_API_USERNAME=120210023
SOURCE_API_PASSWORD=22091998
MYSQL_ROOT_PASSWORD=databridge
MYSQL_DATABASE=databridge_schema
DATABASE_URL="mysql+pymysql://root:${MYSQL_ROOT_PASSWORD}@db:3306/${MYSQL_DATABASE}"
PYTHONPATH=/app
SCHEDULER_DATABASE_URL="mysql+pymysql://root:${MYSQL_ROOT_PASSWORD}@db:3306/scheduler"
``` 

### Arquivo de inicialização do Banco de dados
Certifique-se de copiar a pasta init_db contendo o arquivo init.sql. Esse arquivo é responsável por criar os esquemas necessários para o funcionamento adequado do sistema.


## Como Rodar o Sistema Databridge

1. Certifique-se de ter o Docker e Docker Compose instalados.
2. Execute o seguinte comando para subir os containers (lembre-se de copiar os arquivos .env e init_db/init.sql):
```
docker-compose up -f docker-compose.databridge.yml --build
```
Isso inicializará o Redis, MySQL, o Celery Worker e o Celery Beat. A aplicação será acessível dentro dos containers criados pelo Docker.

3. Caso queira iniciar imediatamente a população do banco de dados, rode o seguinte comando:
```
docker-compose -f docker-compose.databridge.yml exec celery_worker celery -A core.celery_app call scripts.orchestrator.orchestrate_tasks
```
Isso irá chamar a task pelo celery worker que iniciará o processo de popular o banco de dados.

## Estrutura do Docker Compose:
O arquivo docker-compose.yml está configurado da seguinte maneira:

- redis: Container que executa o Redis 6-alpine.
- db: Container que executa o MySQL 8.0 com um volume persistente para dados.
- celery_worker: Container que executa o worker Celery para processamento assíncrono.
- celery_beat: Container que executa o Celery Beat para agendar tarefas periódicas.
Os serviços são configurados para depender uns dos outros (Redis, MySQL) e são iniciados de acordo com as condições de saúde.


## Como Rodar o Sistema Cursos UFCG Completo
Além dos prérequisitos do sistema Databridge, é necessário também o arquivo de configuração do nginx para comunicação do backend e frontend. Para isso, copie o arquivo nginx.conf para a pasta com o arquivo docker-compose.cursos-ufcg.yml.

1. Certifique-se de ter o Docker e Docker Compose instalados.
2. Arquivos necessários:
    * .env: contendo variáveis ambientes
    * init_db/init.sql para inicialização do banco de dados.
    * nginx.conf para configuração do NGINX.
3. Copie os arquivos necessários para o mesmo diretório onde está o arquivo docker-compose.cursos-ufcg.yml:
4. Execute o comando para inicializar os containers:
```
docker-compose -f docker-compose.cursos-ufcg.yml up --build -d
```
Esse comando irá:
* Construir (se necessário) e iniciar todos os containers em segundo plano (-d).
* Configurar o NGINX para redirecionar as requisições entre o backend e frontend.

5. Iniciar população do banco de dados (opcional):

Se desejar popular o banco de dados imediatamente após a configuração, utilize o comando abaixo para chamar a task responsável:
```
docker-compose -f docker-compose.databridge.yml exec celery_worker celery -A core.celery_app call scripts.orchestrator.orchestrate_tasks
```
Esse comando irá acionar o Celery Worker, iniciando o processo de orquestração para popular o banco de dados automaticamente.

4. Acessar a Aplicação

* O frontend estará disponível na sua máquina local na porta 80.
* Certifique-se de que sua rede permite acesso à porta 80 caso esteja utilizando uma máquina remota.