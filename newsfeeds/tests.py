from django.test import TestCase
from newsfeeds.hbase_models import HBaseNewsFeed
from newsfeeds.services import NewsFeedService
from newsfeeds.tasks import fan_out_main_task
from rest_framework.test import APIClient
from utils.test_helpers import TestHelpers
import time


class NewsFeedServiceTests(TestCase):

    def setUp(self):
        TestHelpers.clear_cache()
        self.user1 = TestHelpers.create_user()
        self.user1_client = APIClient()
        self.user1_client.force_authenticate(self.user1)

    def test_get_cached_newsfeeds(self):
        # no newsfeed
        newsfeeds = NewsFeedService.get_newsfeeds_in_redis(self.user1.id)
        self.assertEqual(newsfeeds, [])

        # post tweets
        self.user1_client.post('/api/tweets/', {'content': 'tweet1'})
        self.user1_client.post('/api/tweets/', {'content': 'tweet2'})

        # redis miss and load
        newsfeeds = NewsFeedService.get_newsfeeds_in_redis(self.user1.id)
        newsfeeds = [newsfeed.cached_tweet.content for newsfeed in newsfeeds]
        self.assertEqual(newsfeeds, ['tweet2', 'tweet1'])

        # redis hit
        newsfeeds = NewsFeedService.get_newsfeeds_in_redis(self.user1.id)
        newsfeeds = [newsfeed.cached_tweet.content for newsfeed in newsfeeds]
        self.assertEqual(newsfeeds, ['tweet2', 'tweet1'])

        # extend newsfeed
        self.user1_client.post('/api/tweets/', {'content': 'tweet3'})
        newsfeeds = NewsFeedService.get_newsfeeds_in_redis(self.user1.id)
        newsfeeds = [newsfeed.cached_tweet.content for newsfeed in newsfeeds]
        self.assertEqual(newsfeeds, ['tweet3', 'tweet2', 'tweet1'])


class NewsFeedTaskTests(TestCase):
    def setUp(self):
        TestHelpers.clear_cache()
        self.admin = TestHelpers.create_user()

    def test_fan_out_main_task(self):
        for i in range(1, 5):
            user = TestHelpers.create_user(username=f'user{i}')
            TestHelpers.create_friendship(user, self.admin)
        tweet = TestHelpers.create_tweet(self.admin)
        msg = fan_out_main_task(tweet.id, tweet.user_id, tweet.timestamp)
        self.assertEqual(msg, '4 newsfeeds fan out with 2 batches.')


class NewsFeedsHBaseTests(TestCase):
    def setUp(self):
        TestHelpers.clear_cache()

    @property
    def ts_now(self):
        return int(time.time() * 1000000)

    def test_bulk_create_and_get(self):
        ts = self.ts_now
        bulk_data = [
            {
                'user_id': 1,
                'created_at': ts,
                'tweet_id': 100,
            },
            {
                'user_id': 2,
                'created_at': ts,
                'tweet_id': 100,
            }
        ]

        HBaseNewsFeed.bulk_create(bulk_data=bulk_data)

        instances = HBaseNewsFeed.filter(prefix=(None, ))
        self.assertEqual(len(instances), 2)
        self.assertEqual(instances[0].user_id, 1)
        self.assertEqual(instances[0].created_at, ts)
        self.assertEqual(instances[0].tweet_id, 100)
        self.assertEqual(instances[1].user_id, 2)
        self.assertEqual(instances[1].created_at, ts)
        self.assertEqual(instances[1].tweet_id, 100)
