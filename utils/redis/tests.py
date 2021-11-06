from utils.test_helpers import TestHelpers
from django.test import TestCase
from utils.redis.redis_client import RedisClient


class UtilTests(TestCase):

    def setUp(self):
        TestHelpers.clear_cache()

    def test_redis_client(self):
        conn = RedisClient.get_connection()
        conn.lpush('key', 1)
        conn.lpush('key', 2)
        cached_list = conn.lrange('key', 0, -1)
        self.assertEqual(cached_list, [b'2', b'1'])

        RedisClient.clear()
        cached_list = conn.lrange('key', 0, -1)
        self.assertEqual(cached_list, [])