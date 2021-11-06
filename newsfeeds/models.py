from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from tweets.models import Tweet
from utils.memcached.memcached_helper import MemcachedHelper


# models
class NewsFeed(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    tweet = models.ForeignKey(Tweet, on_delete=models.SET_NULL, null=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    class Meta:
        index_together = (('user', 'created_at'),)
        unique_together = (('user', 'tweet'),)
        ordering = ('user', '-created_at')

    def __str__(self):
        return f'{self.created_at} inbox of {self.user}: {self.tweet}'

    @property
    def cached_tweet(self):
        return MemcachedHelper.get_object_in_memcached(Tweet, self.tweet_id)


# listeners
def extend_newsfeed_in_redis(sender, instance, created, **kwargs):
    if not created:
        return
    from newsfeeds.services import NewsFeedService
    NewsFeedService.extend_newsfeed_in_redis(instance)

# redis
post_save.connect(extend_newsfeed_in_redis, sender=NewsFeed)