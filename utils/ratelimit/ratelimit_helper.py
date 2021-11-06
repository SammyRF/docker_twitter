from utils.redis.redis_client import RedisClient
from datetime import datetime
from django.conf import settings

TIME_STAMP_PATTERN = '{rl_prefix}:{api_path}:{api_name}:{user_id}:'


class TimeRange:
    SECOND = 1
    MINUTE = 2
    HOUR = 3


class RateLimitHelper:

    @classmethod
    def check_limit(cls, api_path, api_name, user_id, hms):
        if not settings.RATE_LIMIT_ENABLE:
            return True

        key = TIME_STAMP_PATTERN.format(
            rl_prefix=settings.RATE_LIMIT_PREFIX,
            api_path=api_path,
            api_name=api_name,
            user_id=user_id,
        )

        h, m, s = hms
        if s > 0 and not cls._check_limit_with_time(key, TimeRange.SECOND, s):
            return False
        if m > 0 and not cls._check_limit_with_time(key, TimeRange.MINUTE, m):
            return False
        if h > 0 and not cls._check_limit_with_time(key, TimeRange.HOUR, h):
            return False
        return True


    @classmethod
    def _check_limit_with_time(cls, key, time_range, allow_count):
        if not time_range in (TimeRange.SECOND, TimeRange.MINUTE, TimeRange.HOUR):
            return True

        # default with Second
        current_time = '%Y%m%d%H%M%S'
        expired_time = 1
        if time_range == TimeRange.MINUTE:
            current_time = datetime.now().strftime('%Y%m%d%H%M')
            expired_time = 60
        elif time_range == TimeRange.HOUR:
            current_time = datetime.now().strftime('%Y%m%d%H')
            expired_time = 3600
        key += current_time

        conn = RedisClient.get_connection()
        if not conn.exists(key):
            conn.set(key, allow_count)  # right now only support minute
            conn.expire(key, expired_time)  # rate limit based on minute
            return True
        return conn.decr(key) > 0


