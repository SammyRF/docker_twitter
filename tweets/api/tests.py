from datetime import timedelta
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from tweets.models import Tweet, TweetPhoto
from utils import helpers
from utils.paginations import EndlessPagination
from utils.test_helpers import TestHelpers

BASE_TWEETS_URL = '/api/tweets/{}'
TWEET_LIST_URL = BASE_TWEETS_URL.format('')
TWEET_CREATE_URL = BASE_TWEETS_URL.format('')
TWEET_RETRIEVE_URL = BASE_TWEETS_URL + '/'


class TweetApiTests(TestCase):

    def setUp(self):
        TestHelpers.clear_cache()

        self.user1 = TestHelpers.create_user()
        self.user2 = TestHelpers.create_user(username='Guest', password='Guest', email='guest@guest.com')
        self.anonymous_client = APIClient()
        self.user1_client = APIClient()
        self.user1_client.force_authenticate(self.user1)
        self.user2_client = APIClient()
        self.user2_client.force_authenticate(self.user2)

    def test_hours_to_now(self):
        user1 = User.objects.create_user(username='user1')
        tweet = Tweet.objects.create(user=user1, content="")
        tweet.created_at = helpers.utc_now() - timedelta(hours=10)
        tweet.save()
        self.assertEqual(tweet.hours_to_now, 10)

    def test_list_api(self):
        tweet1 = TestHelpers.create_tweet(self.user1)
        tweet2 = TestHelpers.create_tweet(self.user1)

        # check used_it is mandatory
        response = self.anonymous_client.get(TWEET_LIST_URL)
        self.assertEqual(response.status_code, 400)

        # check normal case
        response = self.anonymous_client.get(TWEET_LIST_URL, {'user_id': self.user1.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 2)

        # check ordering
        self.assertEqual(response.data['results'][0]['id'], tweet2.id)
        self.assertEqual(response.data['results'][-1]['id'], tweet1.id)

    def test_create_api(self):
        # test anonymous forbidden
        response = self.anonymous_client.post(TWEET_CREATE_URL)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # no content
        response = self.user1_client.post(TWEET_CREATE_URL)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # content size less than 5
        response = self.user1_client.post(TWEET_CREATE_URL, {'content': 'a'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # content size more than 120
        response = self.user1_client.post(TWEET_CREATE_URL, {'content': 'a' * 121})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # normal case
        tweet_count = Tweet.objects.count()
        response = self.user1_client.post(TWEET_CREATE_URL, {'content': 'test content'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['user']['id'], self.user1.id)
        self.assertEqual(Tweet.objects.count(), tweet_count + 1)

    def test_create_with_photos_api(self):
        # empty files allowed
        response = self.user1_client.post(TWEET_CREATE_URL, {
            'content': 'test content',
            'files': [],
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # more than 9 photos not allowed
        files = [
            SimpleUploadedFile(
                name=f'selfie{i}.jpg',
                content=str.encode(f'selfie{i}'),
                content_type='image/jpeg',
            )
            for i in range(10)
        ]
        response = self.user1_client.post(TWEET_CREATE_URL, {
            'content': 'test content',
            'files': files,
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # normal case
        file = SimpleUploadedFile(
            name='selfie.jpg',
            content=str.encode('a fake image'),
            content_type='image/jpeg',
        )
        response = self.user1_client.post(TWEET_CREATE_URL, {
            'content': 'test content',
            'files': [file],
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(TweetPhoto.objects.all().count(), 1)
        self.assertTrue('selfie' in response.data['photo_urls'][0])


    def test_retrieve_api(self):
        # tweet with minus value not exists
        url = TWEET_RETRIEVE_URL.format(-1)
        response = self.anonymous_client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # tweet with comment
        tweet = TestHelpers.create_tweet(self.user1)
        url = TWEET_RETRIEVE_URL.format(tweet.id)
        response = self.anonymous_client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['comments']), 0)

        comment = TestHelpers.create_comment(self.user2, tweet)
        response = self.anonymous_client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['comments']), 1)
        self.assertEqual(response.data['user']['nickname'], None)
        self.assertEqual(response.data['user']['avatar_url'], None)


    def test_retrieve_likes(self):
        tweet = TestHelpers.create_tweet(self.user1)
        url = TWEET_RETRIEVE_URL.format(tweet.id)

        # before like
        response = self.user1_client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['has_liked'], False)
        self.assertEqual(response.data['likes_count'], 0)

        # after like
        TestHelpers.create_like(self.user1, tweet)
        TestHelpers.create_like(self.user2, tweet)
        response = self.user1_client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['has_liked'], True)
        self.assertEqual(response.data['likes_count'], 2)

    def test_retrieve_comments(self):
        tweet = TestHelpers.create_tweet(self.user1)
        url = TWEET_RETRIEVE_URL.format(tweet.id)

        # before like
        response = self.user1_client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['comments_count'], 0)

        # after like
        TestHelpers.create_comment(self.user1, tweet)
        TestHelpers.create_comment(self.user2, tweet)
        response = self.user1_client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['comments_count'], 2)#

    def test_pagination(self):
        page_size = EndlessPagination.page_size

        # create page_size * 2 tweets
        tweets = [
            TestHelpers.create_tweet(self.user1, content='tweet_{}'.format(i))
            for i in range(page_size * 2)
        ][::-1]

        # pull the first page
        response = self.user1_client.get(TWEET_LIST_URL, {'user_id': self.user1.id})
        self.assertEqual(response.data['has_next_page'], True)
        self.assertEqual(len(response.data['results']), page_size)
        self.assertEqual(response.data['results'][0]['id'], tweets[0].id)
        self.assertEqual(response.data['results'][1]['id'], tweets[1].id)
        self.assertEqual(response.data['results'][page_size - 1]['id'], tweets[page_size - 1].id)

        # pull the second page
        response = self.user1_client.get(TWEET_LIST_URL, {
            'created_at__lt': tweets[page_size - 1].created_at,
            'user_id': self.user1.id,
        })
        self.assertEqual(response.data['has_next_page'], False)
        self.assertEqual(len(response.data['results']), page_size)
        self.assertEqual(response.data['results'][0]['id'], tweets[page_size].id)
        self.assertEqual(response.data['results'][1]['id'], tweets[page_size + 1].id)
        self.assertEqual(response.data['results'][page_size - 1]['id'], tweets[2 * page_size - 1].id)

        # pull latest newsfeeds
        response = self.user1_client.get(TWEET_LIST_URL, {
            'created_at__gt': tweets[0].created_at,
            'user_id': self.user1.id,
        })
        self.assertEqual(response.data['has_next_page'], False)
        self.assertEqual(len(response.data['results']), 0)

        new_tweet = TestHelpers.create_tweet(self.user1, 'a new tweet comes in')
        response = self.user1_client.get(TWEET_LIST_URL, {
            'created_at__gt': tweets[0].created_at,
            'user_id': self.user1.id,
        })
        self.assertEqual(response.data['has_next_page'], False)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], new_tweet.id)

