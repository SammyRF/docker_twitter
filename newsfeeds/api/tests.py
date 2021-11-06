from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from tweets.models import Tweet
from utils.paginations import EndlessPagination
from utils.test_helpers import TestHelpers

NEWSFEEDS_URL = '/api/newsfeeds/'
TWEET_CREATE_URL = '/api/tweets/'


class NewsFeedApiTests(TestCase):
    def setUp(self):
        TestHelpers.clear_cache()

        self.user1 = TestHelpers.create_user()
        self.user2 = TestHelpers.create_user(username='Staff', password='Staff', email='staff@staff.com')

        TestHelpers.create_friendship(self.user1, self.user2)
        TestHelpers.create_friendship(self.user2, self.user1)

        self.anonymous_client = APIClient()
        self.user1_client = APIClient()
        self.user1_client.force_authenticate(self.user1)
        self.user2_client = APIClient()
        self.user2_client.force_authenticate(self.user2)

    def test_list_api(self):
        # anonymous is not allowed
        response = self.anonymous_client.get(NEWSFEEDS_URL)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # POST is not allowed
        response = self.user1_client.post(NEWSFEEDS_URL)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        # newsfeeds count is 0 by default
        response = self.user1_client.get(NEWSFEEDS_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 0)

        # newsfeed count of user1 is 1 after user1 post tweet
        self.user1_client.post(TWEET_CREATE_URL, {'content': 'test content'})
        response = self.user1_client.get(NEWSFEEDS_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

        # newsfeed count of user1 is 2 after user2 post tweet, because user1 follow user2
        self.user2_client.post(TWEET_CREATE_URL, {'content': 'test content'})
        response = self.user1_client.get(NEWSFEEDS_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

    def test_pagination(self):
        page_size = EndlessPagination.page_size
        n = page_size * 2
        # create page_size * 2 tweets
        for i in range(page_size * 2):
            self.user1_client.post(TWEET_CREATE_URL, {'content': 'test {}'.format(i)})

        # pull the first page
        response = self.user1_client.get(NEWSFEEDS_URL)
        self.assertEqual(response.data['has_next_page'], True)
        self.assertEqual(len(response.data['results']), page_size)
        self.assertEqual(response.data['results'][0]['tweet']['content'].endswith(str(n - 1)), True)
        self.assertEqual(response.data['results'][1]['tweet']['content'].endswith(str(n - 2)), True)
        first = response.data['results'][0]
        last = response.data['results'][page_size - 1]
        self.assertEqual(last['tweet']['content'].endswith(str(n // 2)), True)

        # pull the second page
        response = self.user1_client.get(
            NEWSFEEDS_URL,
            {'created_at__lt': last['created_at']},
        )
        self.assertEqual(response.data['has_next_page'], False)
        results = response.data['results']
        self.assertEqual(len(results), page_size)
        self.assertEqual(results[0]['tweet']['content'].endswith(str(n // 2 - 1)), True)
        self.assertEqual(results[1]['tweet']['content'].endswith(str(n // 2 - 2)), True)
        self.assertEqual(response.data['results'][page_size - 1]['tweet']['content'].endswith('0'), True)

        # pull latest newsfeeds
        response = self.user1_client.get(
            NEWSFEEDS_URL,
            {'created_at__gt': first['created_at']},
        )
        self.assertEqual(response.data['has_next_page'], False)
        self.assertEqual(len(response.data['results']), 0)

        self.user2_client.post(TWEET_CREATE_URL, {'content': 'new tweet'})
        response = self.user1_client.get(
            NEWSFEEDS_URL,
            {'created_at__gt': first['created_at']},
        )
        self.assertEqual(response.data['has_next_page'], False)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['tweet']['content'], 'new tweet')

    def test_user_cache(self):
        profile = self.user1.profile
        profile.nickname = 'Sam'
        profile.save()
        self.user1_client.post(TWEET_CREATE_URL, {'content': 'test content'})
        response = self.user1_client.get(NEWSFEEDS_URL)

        results = response.data['results']
        self.assertEqual(results[0]['tweet']['user']['username'], 'admin')
        self.assertEqual(results[0]['tweet']['user']['nickname'], 'Sam')

        self.user1.username = 'new admin'
        self.user1.save()
        profile.nickname = 'new Sam'
        profile.save()

        response = self.user1_client.get(NEWSFEEDS_URL)
        results = response.data['results']
        self.assertEqual(results[0]['tweet']['user']['username'], 'new admin')
        self.assertEqual(results[0]['tweet']['user']['nickname'], 'new Sam')

    def test_tweet_cache(self):
        self.user1_client.post(TWEET_CREATE_URL, {'content': 'test content'})
        response = self.user1_client.get(NEWSFEEDS_URL)
        results = response.data['results']
        self.assertEqual(results[0]['tweet']['user']['username'], 'admin')
        self.assertEqual(results[0]['tweet']['content'], 'test content')
        tweet_id = results[0]['tweet']['id']

        # update username
        self.user1.username = 'new admin'
        self.user1.save()
        response = self.user1_client.get(NEWSFEEDS_URL)
        results = response.data['results']
        self.assertEqual(results[0]['tweet']['user']['username'], 'new admin')

        # update content
        tweet = Tweet.objects.get(id=tweet_id)
        tweet.content = 'new content'
        tweet.save()
        response = self.user1_client.get(NEWSFEEDS_URL)
        results = response.data['results']
        self.assertEqual(results[0]['tweet']['content'], 'new content')