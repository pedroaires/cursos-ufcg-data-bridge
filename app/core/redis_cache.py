import redis
import json
from config.celery_config import redis_cache_config

class RedisCache:
    def __init__(self):
        self.redis = redis.Redis(
            host=redis_cache_config['host'],
            port=redis_cache_config['port'],
            db=redis_cache_config['db']
        )

    def set_data(self, key, value, expire=None):
        self.redis.set(key, json.dumps(value), ex=expire)

    def get_data(self, key):
        data = self.redis.get(key)
        return json.loads(data) if data else None

    def delete_data(self, key):
        self.redis.delete(key)