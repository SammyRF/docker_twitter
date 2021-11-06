from django.conf import settings
import redis


class RedisClient:
    _conn = None

    @classmethod
    def get_connection(cls):
        if cls._conn:
            return cls._conn
        cls._conn = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
        )
        return cls._conn

    @classmethod
    def clear(cls):
        if not settings.TESTING:
            raise Exception("You can not flush DB in product environment")
        conn = cls.get_connection()
        conn.flushdb()