from utils.hbase import models
from utils.memcached.memcached_helper import MemcachedHelper
from tweets.models import Tweet
from django.contrib.auth.models import User


class HBaseNewsFeed(models.HBaseModel):
    user_id = models.IntegerField(reverse=True)
    created_at = models.TimestampField()
    tweet_id = models.IntegerField(column_family='cf')

    class Meta:
        table_name = 'twitter_newsfeeds'
        row_key = ('user_id', 'created_at')

    def __str__(self):
        return f'{self.created_at} inbox of {self.user_id}: {self.tweet_id}'

    @property
    def cached_tweet(self):
        return MemcachedHelper.get_object_in_memcached(Tweet, self.tweet_id)

    @property
    def cached_user(self):
        return MemcachedHelper.get_object_in_memcached(User, self.user_id)