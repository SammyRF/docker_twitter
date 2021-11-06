from newsfeeds.hbase_models import HBaseNewsFeed
from newsfeeds.models import NewsFeed
from newsfeeds.tasks import fan_out_main_task
from utils.gatekeeper.models import GateKeeper
from utils.redis.redis_helper import RedisHelper, USER_NEWSFEEDS_PATTERN


class NewsFeedService:

    @classmethod
    def create(cls, **kwargs):
        if not GateKeeper.is_switch_on('switch_newsfeed_to_hbase'):
            # create object in mysql
            newsfeed = NewsFeed.objects.create(**kwargs)
        else:
            # create object in hbase
            newsfeed = HBaseNewsFeed.create(**kwargs)
            cls.extend_newsfeed_in_redis(newsfeed)
        return newsfeed

    @classmethod
    def bulk_create(cls, newsfeeds_data):
        if not GateKeeper.is_switch_on('switch_newsfeed_to_hbase'):
            # create objects in mysql
            newsfeeds = [NewsFeed(**data) for data in newsfeeds_data]
            NewsFeed.objects.bulk_create(newsfeeds)
        else:
            # create objects in hbase
            newsfeeds = HBaseNewsFeed.bulk_create(newsfeeds_data)
        # bulk will not trigger signal
        for newsfeed in newsfeeds:
            cls.extend_newsfeed_in_redis(newsfeed)
        return newsfeeds

    @classmethod
    def fan_out(cls, tweet):
        fan_out_main_task.delay(tweet.id, tweet.user_id, tweet.timestamp)

    @classmethod
    def get_newsfeeds_in_redis(cls, user_id):
        key = USER_NEWSFEEDS_PATTERN.format(user_id=user_id)
        if not GateKeeper.is_switch_on('switch_newsfeed_to_hbase'):
            # get objects in mysql
            queryset = NewsFeed.objects.filter(user_id=user_id).order_by('-created_at')
            return RedisHelper.get_objects_in_redis_from_sql(key, queryset)
        else:
            # get objects in HBase
            query_func = lambda limit: HBaseNewsFeed.filter(prefix=(user_id, None), limit=limit, reverse=True)
            return RedisHelper.get_objects_in_redis_from_hbase(key, query_func)

    @classmethod
    def extend_newsfeed_in_redis(cls, newsfeed):
        key = USER_NEWSFEEDS_PATTERN.format(user_id=newsfeed.user_id)
        if not GateKeeper.is_switch_on('switch_newsfeed_to_hbase'):
            # get object in mysql
            queryset = NewsFeed.objects.filter(user_id=newsfeed.user_id).order_by('-created_at')
            RedisHelper.extend_object_in_redis_from_sql(key, newsfeed, queryset)
        else:
            # get object in HBase
            query_func = lambda limit: HBaseNewsFeed.filter(prefix=(newsfeed.user_id, None), limit=limit, reverse=True)
            return RedisHelper.extend_object_in_redis_from_hbase(key, newsfeed, query_func)