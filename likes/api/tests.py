from django.test import TestCase
from utils.test_helpers import TestHelpers
from rest_framework.test import APIClient
from rest_framework import status

BASE_LIKE_URL = '/api/likes/'
CANCEL_LIKE_URL = '/api/likes/cancel/'


class LikeApiTests(TestCase):
    def setUp(self):
        TestHelpers.clear_cache()

        self.anonymous_client = APIClient()

        self.admin = TestHelpers.create_user()
        self.admin_client = APIClient()
        self.admin_client.force_authenticate(self.admin)
        self.user1 = TestHelpers.create_user('user1')
        self.user1_client = APIClient()
        self.user1_client.force_authenticate(self.user1)

        self.tweet = TestHelpers.create_tweet(self.admin)
        self.comment = TestHelpers.create_comment(self.user1, self.tweet)

    def test_like_tweet_api(self):
        # ANONYMOUS is not allow to like
        response = self.anonymous_client.post(
            path=BASE_LIKE_URL,
            data = {'content_type': 'tweet', 'object_id': self.tweet.id},
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # 'get' is not allowed
        response = self.user1_client.get(
            path=BASE_LIKE_URL,
            data={'content_type': 'tweet', 'object_id': self.tweet.id},
        )
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        # normal case
        response = self.user1_client.post(
            path=BASE_LIKE_URL,
            data={'content_type': 'tweet', 'object_id': self.tweet.id},
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.tweet.like_set.count(), 1)

        # duplicated like will be ignored
        response = self.user1_client.post(
            path=BASE_LIKE_URL,
            data={'content_type': 'tweet', 'object_id': self.tweet.id},
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.tweet.like_set.count(), 1)

        # different likes
        response = self.admin_client.post(
            path=BASE_LIKE_URL,
            data={'content_type': 'tweet', 'object_id': self.tweet.id},
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.tweet.like_set.count(), 2)

    def test_like_comment_api(self):
        # ANONYMOUS is not allow to like
        response = self.anonymous_client.post(
            path=BASE_LIKE_URL,
            data={'content_type': 'comment', 'object_id': self.comment.id},
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # 'get' is not allowed
        response = self.user1_client.get(
            path=BASE_LIKE_URL,
            data={'content_type': 'comment', 'object_id': self.comment.id},
        )
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        # normal case
        response = self.user1_client.post(
            path=BASE_LIKE_URL,
            data={'content_type': 'comment', 'object_id': self.comment.id},
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.comment.like_set.count(), 1)

        # duplicated like will be ignored
        response = self.user1_client.post(
            path=BASE_LIKE_URL,
            data={'content_type': 'comment', 'object_id': self.comment.id},
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.comment.like_set.count(), 1)

        # different likes
        response = self.admin_client.post(
            path=BASE_LIKE_URL,
            data={'content_type': 'comment', 'object_id': self.comment.id},
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.comment.like_set.count(), 2)

    def test_cancel_like_api(self):
        like_comment_data = {'content_type': 'comment', 'object_id': self.comment.id}
        like_tweet_data = {'content_type': 'tweet', 'object_id': self.tweet.id}
        self.admin_client.post(BASE_LIKE_URL, like_comment_data)
        self.user1_client.post(BASE_LIKE_URL, like_tweet_data)
        self.assertEqual(self.tweet.like_set.count(), 1)
        self.assertEqual(self.comment.like_set.count(), 1)

        # ANONYMOUS is not allowed
        response = self.anonymous_client.post(CANCEL_LIKE_URL, like_comment_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        response = self.anonymous_client.post(CANCEL_LIKE_URL, like_tweet_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # 'Get' not allowed
        response = self.user1_client.get(CANCEL_LIKE_URL, like_comment_data)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        response = self.admin_client.get(CANCEL_LIKE_URL, like_tweet_data)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        # other user not allowed
        response = self.user1_client.post(CANCEL_LIKE_URL, like_comment_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        response = self.admin_client.post(CANCEL_LIKE_URL, like_tweet_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # normal case
        response = self.admin_client.post(CANCEL_LIKE_URL, like_comment_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.comment.like_set.count(), 0)
        response = self.user1_client.post(CANCEL_LIKE_URL, like_tweet_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.tweet.like_set.count(), 0)

    def test_likes_count_with_cache(self):
        tweet_url = '/api/tweets/{}/'.format(self.tweet.id)
        response = self.admin_client.get(tweet_url)
        self.assertEqual(self.tweet.likes_count, 0)
        self.assertEqual(response.data['likes_count'], 0)

        data = {'object_id': self.tweet.id, 'content_type': 'tweet'}
        # first like
        self.admin_client.post(BASE_LIKE_URL, data)
        response = self.admin_client.get(tweet_url)
        self.assertEqual(response.data['likes_count'], 1)
        self.tweet.refresh_from_db()
        self.assertEqual(self.tweet.likes_count, 1)

        # second like
        self.user1_client.post(BASE_LIKE_URL, data)
        response = self.admin_client.get(tweet_url)
        self.assertEqual(response.data['likes_count'], 2)
        self.tweet.refresh_from_db()
        self.assertEqual(self.tweet.likes_count, 2)

        # cancel second like
        response = self.user1_client.post(CANCEL_LIKE_URL, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.admin_client.get(tweet_url)
        self.assertEqual(response.data['likes_count'], 1)
        self.tweet.refresh_from_db()
        self.assertEqual(self.tweet.likes_count, 1)
