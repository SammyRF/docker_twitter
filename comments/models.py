from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models.signals import pre_delete, post_save
from likes.models import Like
from tweets.models import Tweet
from utils.memcached.memcached_helper import MemcachedHelper
from utils.redis.redis_helper import RedisHelper

# models
class Comment(models.Model):
    content = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    tweet = models.ForeignKey(Tweet, on_delete=models.SET_NULL, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    likes_count = models.IntegerField(default=0, null=True)

    class Meta:
        index_together = (('tweet', 'created_at'),)
        ordering = ('-created_at',)

    def __str__(self):
        return f'{self.created_at} {self.user}@{self.tweet}: {self.content}'

    @property
    def like_set(self):
        return Like.objects.filter(
            content_type=ContentType.objects.get_for_model(self.__class__),
            object_id=self.id,
        ).order_by('-created_at')

    @property
    def cached_user(self):
        return MemcachedHelper.get_object_in_memcached(User, self.user_id)

# listeners
def incr_comments_count_in_redis(sender, instance, created, **kwargs):
    from tweets.models import Tweet
    from django.db.models import F

    if not created:
        return

    Tweet.objects.filter(id=instance.tweet_id).update(comments_count=F('comments_count') + 1)
    RedisHelper.incr_count_in_redis(instance.tweet, 'comments_count')

def decr_comments_count_in_redis(sender, instance, **kwargs):
    from tweets.models import Tweet
    from django.db.models import F

    Tweet.objects.filter(id=instance.tweet_id).update(comments_count=F('comments_count') - 1)
    RedisHelper.decr_count_in_redis(instance.tweet, 'comments_count')

# redis
post_save.connect(incr_comments_count_in_redis, sender=Comment)
pre_delete.connect(decr_comments_count_in_redis, sender=Comment)
