from tweets.models import Tweet
from utils.redis.redis_helper import RedisHelper, USER_TWEETS_PATTERN


class TweetService:

    @classmethod
    def get_tweets_in_redis(cls, user_id):
        queryset = Tweet.objects.filter(user_id=user_id).order_by('-created_at')
        key = USER_TWEETS_PATTERN.format(user_id=user_id)
        return RedisHelper.get_objects_in_redis_from_sql(key, queryset)

    @classmethod
    def extend_tweet_in_redis(cls, tweet):
        queryset = Tweet.objects.filter(user_id=tweet.user_id).order_by('-created_at')
        key = USER_TWEETS_PATTERN.format(user_id=tweet.user_id)
        RedisHelper.extend_object_in_redis_from_sql(key, tweet, queryset)