from comments.models import Comment
from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient
from utils.test_helpers import TestHelpers

BASE_COMMENT_URL = '/api/comments/{}'
CREATE_COMMENT_URL = BASE_COMMENT_URL.format('')
DELETE_COMMENT_URL = BASE_COMMENT_URL + '/'
UPDATE_COMMENT_URL = BASE_COMMENT_URL + '/'
LIST_COMMENT_URL = BASE_COMMENT_URL.format('')
RETRIEVE_COMMENT_URL = BASE_COMMENT_URL + '/'

class CommentApiTests(TestCase):

    def setUp(self):
        TestHelpers.clear_cache()

        self.user1 = TestHelpers.create_user()
        self.user2 = TestHelpers.create_user(username='Staff', password='Staff', email='staff@staff.com')

        self.anonymous_client = APIClient()
        self.user1_client = APIClient()
        self.user1_client.force_authenticate(self.user1)
        self.user2_client = APIClient()
        self.user2_client.force_authenticate(self.user2)

        self.tweet1 = TestHelpers.create_tweet(self.user1)
        self.tweet2 = TestHelpers.create_tweet(self.user2)

    def test_create_api(self):
        # ANONYMOUS is not allowed
        response = self.anonymous_client.post(CREATE_COMMENT_URL)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # 'tweet_id' and 'content' are required
        response = self.user1_client.post(CREATE_COMMENT_URL)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response = self.user1_client.post(CREATE_COMMENT_URL, {'tweet_id': self.tweet1.id})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response = self.user1_client.post(CREATE_COMMENT_URL, {'content': 'test content'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # content out of size
        response = self.user1_client.post(CREATE_COMMENT_URL, data={
            'tweet_id': self.tweet1.id,
            'content': '1' * 256,
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual('content' in response.data['errors'], True)

        # normal case
        response = self.user1_client.post(CREATE_COMMENT_URL, {
            'tweet_id': self.tweet1.id,
            'content': '1',
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['user']['id'], self.user1.id)
        self.assertEqual(response.data['tweet_id'], self.tweet1.id)
        self.assertEqual(response.data['content'], '1')

    def test_destroy_api(self):
        comment = TestHelpers.create_comment(self.user1, self.tweet1, 'test comment')
        url = DELETE_COMMENT_URL.format(comment.id)

        # ANONYMOUS is not allowed
        response = self.anonymous_client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Delete by none owner is not allowed
        response = self.user2_client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # normal case
        count = Comment.objects.count()
        response = self.user1_client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Comment.objects.count(), count - 1)

    def test_update_api(self):
        comment = TestHelpers.create_comment(self.user1, self.tweet1, 'original')
        another_tweet = TestHelpers.create_tweet(self.user2)
        url = UPDATE_COMMENT_URL.format(comment.id)

        # ANONYMOUS is not allowed
        response = self.anonymous_client.put(url, {'content': 'new'})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Update by none owner is not allowed
        response = self.user2_client.put(url, {'content': 'new'})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        comment.refresh_from_db()
        self.assertNotEqual(comment.content, 'new')

        # normal case
        before_updated_at = comment.updated_at
        before_created_at = comment.created_at
        now = timezone.now()
        response = self.user1_client.put(url, {
            'content': 'new',
            'user_id': self.user2.id,
            'tweet_id': another_tweet.id,
            'created_at': now,
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        comment.refresh_from_db()
        self.assertEqual(comment.content, 'new')
        self.assertEqual(comment.user, self.user1)
        self.assertEqual(comment.tweet, self.tweet1)
        self.assertEqual(comment.created_at, before_created_at)
        self.assertNotEqual(comment.created_at, now)
        self.assertNotEqual(comment.updated_at, before_updated_at)

    def test_list_api(self):
        # 'tweet_id' is required
        response = self.anonymous_client.get(LIST_COMMENT_URL)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # no comments case
        response = self.anonymous_client.get(LIST_COMMENT_URL, {
            'tweet_id': self.tweet1.id,
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['comments']), 0)

        # comments sorted by 'create_by'
        TestHelpers.create_comment(self.user1, self.tweet1, '1')
        TestHelpers.create_comment(self.user2, self.tweet1, '2')
        TestHelpers.create_comment(self.user2, TestHelpers.create_tweet(self.user2), '3')
        response = self.anonymous_client.get(LIST_COMMENT_URL, {
            'tweet_id': self.tweet1.id,
        })
        self.assertEqual(len(response.data['comments']), 2)
        self.assertEqual(response.data['comments'][0]['content'], '1')
        self.assertEqual(response.data['comments'][1]['content'], '2')

        # only 'tweet_id' is required
        response = self.anonymous_client.get(LIST_COMMENT_URL, {
            'tweet_id': self.tweet1.id,
            'user_id': self.user1.id,
        })
        self.assertEqual(len(response.data['comments']), 2)

    def test_retrieve_api(self):
        comment = TestHelpers.create_comment(self.user1, self.tweet1, 'test comment')
        url = RETRIEVE_COMMENT_URL.format(comment.id)

        # ANONYMOUS is not allowed
        response = self.anonymous_client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # normal case
        response = self.user1_client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['content'], 'test comment')

    def test_like_api(self):
        comment = TestHelpers.create_comment(self.user1, self.tweet1, 'test comment')
        url = RETRIEVE_COMMENT_URL.format(comment.id)

        # before like
        response = self.user1_client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['has_like'], False)
        self.assertEqual(response.data['likes_count'], 0)

        # after like
        TestHelpers.create_like(self.user1, comment)
        TestHelpers.create_like(self.user2, comment)
        response = self.user1_client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['has_like'], True)
        self.assertEqual(response.data['likes_count'], 2)

    def test_comments_count_with_cache(self):
        tweet_url = '/api/tweets/{}/'.format(self.tweet1.id)
        response = self.user1_client.get(tweet_url)
        self.assertEqual(self.tweet1.comments_count, 0)
        self.assertEqual(response.data['comments_count'], 0)

        # first comment
        data = {'tweet_id': self.tweet1.id, 'content': 'user1 comment'}
        self.user1_client.post(CREATE_COMMENT_URL, data)
        response = self.user1_client.get(tweet_url)
        self.assertEqual(response.data['comments_count'], 1)
        self.tweet1.refresh_from_db()
        self.assertEqual(self.tweet1.comments_count, 1)

        # second comment
        data = {'tweet_id': self.tweet1.id, 'content': 'user2 comment'}
        comment_response = self.user2_client.post(CREATE_COMMENT_URL, data)
        response = self.user1_client.get(tweet_url)
        self.assertEqual(response.data['comments_count'], 2)
        self.tweet1.refresh_from_db()
        self.assertEqual(self.tweet1.comments_count, 2)

        # update comment should not change comments count
        comment_id = comment_response.data['id']
        response = self.user2_client.put(UPDATE_COMMENT_URL.format(comment_id), {'content': 'changed comment'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.user1_client.get(tweet_url)
        self.assertEqual(response.data['comments_count'], 2)
        self.tweet1.refresh_from_db()
        self.assertEqual(self.tweet1.comments_count, 2)

        # delete second comment
        comment_id = comment_response.data['id']
        response = self.user2_client.delete(DELETE_COMMENT_URL.format(comment_id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.user1_client.get(tweet_url)
        self.assertEqual(response.data['comments_count'], 1)
        self.tweet1.refresh_from_db()
        self.assertEqual(self.tweet1.comments_count, 1)