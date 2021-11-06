from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models.signals import pre_delete, post_save
from likes.models import Like
from tweets.constants import TweetPhotoStatus, TWEET_PHOTO_STATUS_CHOICES
from utils import helpers
from utils.memcached.memcached_helper import MemcachedHelper, invalidate_object_in_memcached


# models
class Tweet(models.Model):
    content = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    likes_count = models.IntegerField(default=0, null=True)
    comments_count = models.IntegerField(default=0, null=True)

    class Meta:
        index_together = (('user', 'created_at'), )
        ordering = ('user', '-created_at')

    @property
    def hours_to_now(self):
        return (helpers.utc_now() - self.created_at).seconds // 3600

    def __str__(self):
        return f'{self.created_at} {self.user}: {self.content}'

    @property
    def like_set(self):
        return Like.objects.filter(
            content_type=ContentType.objects.get_for_model(self.__class__),
            object_id=self.id,
        ).order_by('-created_at')

    @property
    def cached_user(self):
        return MemcachedHelper.get_object_in_memcached(User, self.user_id)

    @property
    def timestamp(self):
        return int(self.created_at.timestamp() * 1000000)


class TweetPhoto(models.Model):
    tweet = models.ForeignKey(Tweet, on_delete=models.SET_NULL, null=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    file = models.FileField()
    order = models.IntegerField(default=0)
    status = models.IntegerField(
        default=TweetPhotoStatus.PENDING,
        choices=TWEET_PHOTO_STATUS_CHOICES,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True)

    class Meta:
        index_together = (
            ('user', 'created_at'),
            ('tweet', 'order'),
        )

    def __str__(self):
        return f'{self.tweet_id}: {self.file}'


# listeners
def extend_tweet_in_redis(sender, instance, created, **kwargs):
    if not created:
        return
    from tweets.services import TweetService
    TweetService.extend_tweet_in_redis(instance)

# memcached
post_save.connect(invalidate_object_in_memcached, sender=Tweet)
pre_delete.connect(invalidate_object_in_memcached, sender=Tweet)

# redis
post_save.connect(extend_tweet_in_redis, sender=Tweet)