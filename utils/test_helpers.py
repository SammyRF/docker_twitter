from accounts.models import UserProfile
from comments.models import Comment
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from friendships.services import FriendshipService
from likes.models import Like
from tweets.models import Tweet
from utils.gatekeeper.models import GateKeeper
from utils.hbase.hbase_client import HBaseClient
from utils.memcached.memcached_helper import project_memcached
from utils.redis.redis_client import RedisClient


class TestHelpers:
    @classmethod
    def clear_cache(cls):
        project_memcached.clear()
        RedisClient.clear()
        HBaseClient.clear()
        GateKeeper.turn_on('switch_friendship_to_hbase')
        GateKeeper.turn_on('switch_newsfeed_to_hbase')


    @classmethod
    def create_user(cls, username='admin', password='correct password', email='admin@admin.com'):
        return User.objects.create_user(
            username=username,
            password=password,
            email=email
        )

    @classmethod
    def create_tweet(cls, user, content='default tweet content'):
        return Tweet.objects.create(user=user, content=content)

    @classmethod
    def create_friendship(cls, from_user, to_user):
        return FriendshipService.follow(from_user_id=from_user.id, to_user_id=to_user.id)

    @classmethod
    def create_comment(cls, user, tweet, content="default comment content"):
        return Comment.objects.create(user=user, tweet=tweet, content=content)

    @classmethod
    def create_like(cls, user, target):
        return Like.objects.create(
            user=user,
            content_type=ContentType.objects.get_for_model(target.__class__),
            object_id=target.id,
        )

    @classmethod
    def create_profile(cls, user, nickname='Sam'):
        return UserProfile.objects.create(user=user, nickname=nickname)

