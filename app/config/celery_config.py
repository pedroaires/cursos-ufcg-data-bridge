broker_url = "redis://localhost:6379/0"
result_backend = "redis://localhost:6379/0"

task_serializer = "json"
result_serializer = "json"
accept_content = ["json"]

timezone = "America/Sao_Paulo"
enable_utc = True

result_expires = 3600

redis_cache = {
    'host': 'localhost',
    'port': 6380,
    'db': 0,
}