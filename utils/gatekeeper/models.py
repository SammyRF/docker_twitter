from utils.redis.redis_client import RedisClient


class GateKeeper:

    @classmethod
    def get(cls, gk_name):
        conn = RedisClient.get_connection()
        name = f'gatekeeper:{gk_name}'
        if not conn.exists(name):
            return {'percent': 0, 'description': ''}
        redis_data = conn.hgetall(name)
        return {
            'percent': int(redis_data.get(b'percent', 0)),
            'description': str(redis_data.get(b'description', '')),
        }

    @classmethod
    def set(cls, gk_name, key, value):
        conn = RedisClient.get_connection()
        name = f'gatekeeper:{gk_name}'
        conn.hset(name, key, value)

    @classmethod
    def is_switch_on(cls, gk_name):
        return cls.get(gk_name)['percent'] == 100

    @classmethod
    def turn_on(cls, gk_name):
        cls.set(gk_name, 'percent', 100)

    @classmethod
    def uid_in_gk(cls, uid, gk_name):
        return (uid % 100) < cls.get(gk_name)['percent']