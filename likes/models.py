from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models.signals import pre_delete, post_save
from utils.memcached.memcached_helper import MemcachedHelper
from utils.redis.redis_helper import RedisHelper


# models
class Like(models.Model):
    content_object = GenericForeignKey('content_type', 'object_id')
    content_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    object_id = models.PositiveIntegerField()
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    class Meta:
        unique_together = (('user', 'content_type', 'object_id'),)
        index_together = (('content_type', 'object_id', 'created_at'),)

    def __str__(self):
        return f'{self.created_at} {self.user} likes {self.content_type} {self.id}'

    @property
    def cached_user(self):
        return MemcachedHelper.get_object_in_memcached(User, self.user_id)


# listeners
def incr_likes_count_in_redis(sender, instance, created, **kwargs):
    from tweets.models import Tweet
    from comments.models import Comment
    from django.db.models import F

    if not created:
        return

    if isinstance(instance.content_object, Tweet):
        Tweet.objects.filter(id=instance.object_id).update(likes_count=F('likes_count') + 1)
        RedisHelper.incr_count_in_redis(instance.content_object, 'likes_count')

    if isinstance(instance.content_object, Comment):
        Tweet.objects.filter(id=instance.object_id).update(likes_count=F('likes_count') + 1)
        RedisHelper.incr_count_in_redis(instance.content_object, 'likes_count')

def decr_likes_count_in_redis(sender, instance, **kwargs):
    from tweets.models import Tweet
    from comments.models import Comment
    from django.db.models import F

    if isinstance(instance.content_object, Tweet):
        Tweet.objects.filter(id=instance.object_id).update(likes_count=F('likes_count') - 1)
        RedisHelper.decr_count_in_redis(instance.content_object, 'likes_count')

    if isinstance(instance.content_object, Comment):
        Tweet.objects.filter(id=instance.object_id).update(likes_count=F('likes_count') - 1)
        RedisHelper.decr_count_in_redis(instance.content_object, 'likes_count')


# redis
post_save.connect(incr_likes_count_in_redis, sender=Like)
pre_delete.connect(decr_likes_count_in_redis, sender=Like)