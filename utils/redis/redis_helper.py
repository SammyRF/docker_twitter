from django.conf import settings
from utils.redis.redis_client import RedisClient
from utils.redis.redis_serializers import DjangoModelSerializer, HBaseModelSerializer

USER_TWEETS_PATTERN = 'user_tweets:{user_id}'
USER_NEWSFEEDS_PATTERN = 'user_newsfeeds:{user_id}'


class RedisHelper:

    @classmethod
    def get_objects_in_redis_from_sql(cls, key, queryset):
        conn = RedisClient.get_connection()

        # if redis hit
        if conn.exists(key):
            serialized_list = conn.lrange(key, 0, -1)
            return [DjangoModelSerializer.deserialize(obj_data) for obj_data in serialized_list]

        # when not hit, load objects into redis
        objects = list(queryset[:settings.REDIS_LIST_LENGTH_LIMIT])
        serialized_list = [DjangoModelSerializer.serialize(obj) for obj in objects]
        if serialized_list:
            conn.rpush(key, *serialized_list)
            conn.expire(key, settings.REDIS_KEY_EXPIRE_TIME)
        return objects

    @classmethod
    def get_objects_in_redis_from_hbase(cls, key, query_func):
        conn = RedisClient.get_connection()

        # if redis hit
        if conn.exists(key):
            serialized_list = conn.lrange(key, 0, -1)
            return [HBaseModelSerializer.deserialize(obj_data) for obj_data in serialized_list]

        # when not hit, load objects into redis
        objects = query_func(settings.REDIS_LIST_LENGTH_LIMIT)
        serialized_list = [HBaseModelSerializer.serialize(obj) for obj in objects]
        if serialized_list:
            conn.rpush(key, *serialized_list)
            conn.expire(key, settings.REDIS_KEY_EXPIRE_TIME)
        return objects

    @classmethod
    def extend_object_in_redis_from_sql(cls, key, obj, queryset):
        conn = RedisClient.get_connection()

        # if redis hit
        if conn.exists(key):
            serialized_obj = DjangoModelSerializer.serialize(obj)
            conn.lpush(key, serialized_obj)
            conn.ltrim(key, 0, settings.REDIS_LIST_LENGTH_LIMIT - 1)
            return

        # if not hit, load from DB
        objects = list(queryset[:settings.REDIS_LIST_LENGTH_LIMIT])
        serialized_list = [DjangoModelSerializer.serialize(obj) for obj in objects]
        if serialized_list:
            conn.rpush(key, *serialized_list)
            conn.expire(key, settings.REDIS_KEY_EXPIRE_TIME)

    @classmethod
    def extend_object_in_redis_from_hbase(cls, key, obj, query_func):
        conn = RedisClient.get_connection()

        # if redis hit
        if conn.exists(key):
            serialized_obj = HBaseModelSerializer.serialize(obj)
            conn.lpush(key, serialized_obj)
            conn.ltrim(key, 0, settings.REDIS_LIST_LENGTH_LIMIT - 1)
            return

        # if not hit, load from DB
        objects = query_func(settings.REDIS_LIST_LENGTH_LIMIT)
        serialized_list = [HBaseModelSerializer.serialize(obj) for obj in objects]
        if serialized_list:
            conn.rpush(key, *serialized_list)
            conn.expire(key, settings.REDIS_KEY_EXPIRE_TIME)

    @classmethod
    def get_count_key(cls, obj, attr):
        return f'{obj.__class__.__name__}.{attr}:{obj.id}'

    @classmethod
    def incr_count_in_redis(cls, obj, attr):
        conn = RedisClient.get_connection()
        key = cls.get_count_key(obj, attr)
        if not conn.exists(key):
            obj.refresh_from_db()
            conn.set(key, getattr(obj, attr))
            conn.expire(key, settings.REDIS_KEY_EXPIRE_TIME)
            return getattr(obj, attr)
        return conn.incr(key)

    @classmethod
    def decr_count_in_redis(cls, obj, attr):
        conn = RedisClient.get_connection()
        key = cls.get_count_key(obj, attr)
        if not conn.exists(key):
            obj.refresh_from_db()
            conn.set(key, getattr(obj, attr))
            conn.expire(key, settings.REDIS_KEY_EXPIRE_TIME)
            return getattr(obj, attr)
        return conn.decr(key)

    @classmethod
    def get_count_in_redis(cls, obj, attr):
        conn = RedisClient.get_connection()
        key = cls.get_count_key(obj, attr)
        if not conn.exists(key):
            obj.refresh_from_db()
            conn.set(key, getattr(obj, attr))
            conn.expire(key, settings.REDIS_KEY_EXPIRE_TIME)
            return getattr(obj, attr)
        return int(conn.get(key))
