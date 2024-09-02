FROM python:3.8-slim

WORKDIR /app

RUN apt-get update && apt-get install -y default-mysql-client

COPY app/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY app /app

CMD ["celery", "-A", "core.celery_app", "worker", "--loglevel=info"]
