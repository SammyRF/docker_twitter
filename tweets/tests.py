from django.test import TestCase
from tweets.models import TweetPhoto
from tweets.services import TweetService
from utils.redis.redis_client import RedisClient
from utils.redis.redis_serializers import DjangoModelSerializer
from utils.test_helpers import TestHelpers


class TweetPhotoTests(TestCase):
    def setUp(self):
        TestHelpers.clear_cache()
        
        self.admin = TestHelpers.create_user()
        self.tweet = TestHelpers.create_tweet(self.admin)

    def test_tweetphoto(self):
        tweet_photo = TweetPhoto.objects.create(
            user=self.admin,
            tweet=self.tweet,
        )
        self.assertEqual(tweet_photo.user, self.admin)
        self.assertEqual(tweet_photo.tweet, self.tweet)
        self.assertEqual(TweetPhoto.objects.all().count(), 1)

    def test_cache_tweet_in_redis(self):
        conn = RedisClient.get_connection()
        serializerd_data = DjangoModelSerializer.serialize(self.tweet)
        conn.set(f'tweet:{self.tweet.id}', serializerd_data)
        data = conn.get(f'nothing')
        self.assertEqual(data, None)

        data = conn.get(f'tweet:{self.tweet.id}')
        cached_tweet = DjangoModelSerializer.deserialize(data)
        self.assertEqual(self.tweet, cached_tweet)


class TweetServiceTests(TestCase):

    def setUp(self):
        TestHelpers.clear_cache()
        self.user1 = TestHelpers.create_user()

    def test_get_cached_tweets(self):
        # no tweets
        tweets = TweetService.get_tweets_in_redis(self.user1.id)
        self.assertEqual(tweets, [])

        # create tweets
        tweet1 = TestHelpers.create_tweet(self.user1, 'tweet1')
        tweet2 = TestHelpers.create_tweet(self.user1, 'tweet2')

        # redis miss
        tweets = TweetService.get_tweets_in_redis(self.user1.id)
        self.assertEqual(tweets, [tweet2, tweet1])

        # redis hit
        tweets = TweetService.get_tweets_in_redis(self.user1.id)
        self.assertEqual(tweets, [tweet2, tweet1])

        # redis extend object
        tweet3 = TestHelpers.create_tweet(self.user1, 'tweet3')
        tweets = TweetService.get_tweets_in_redis(self.user1.id)
        self.assertEqual(tweets, [tweet3, tweet2, tweet1])




