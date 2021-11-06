from django.test import TestCase
from inbox.services import NotificationSerivce
from notifications.models import Notification
from rest_framework import status
from rest_framework.test import APIClient
from utils.test_helpers import TestHelpers

CREATE_LIKE_URL = '/api/likes/'
CREATE_COMMENT_URL = '/api/comments/'
UNREAD_COUNT_URL = '/api/notifications/unread-count/'
MARK_ALL_AS_READ_URL = '/api/notifications/mark-all-as-read/'
UPDATE_NOTIFICATION_URL = '/api/notifications/{}/'


class NotificationsServiceTests(TestCase):

    def setUp(self):
        TestHelpers.clear_cache()

        self.admin = TestHelpers.create_user()
        self.admin_client = APIClient()
        self.admin_client.force_authenticate(self.admin)

        self.user1 = TestHelpers.create_user('user1')
        self.user1_client = APIClient()
        self.user1_client.force_authenticate(self.user1)

        self.anonymous_client = APIClient()

    def test_notify_like_api(self):
        tweet = TestHelpers.create_tweet(self.admin)
        comment = TestHelpers.create_comment(self.admin, tweet)

        # notify when someone likes your tweet
        response = self.user1_client.post(CREATE_LIKE_URL, {
            'content_type': 'tweet',
            'object_id': tweet.id,
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Notification.objects.all().count(), 1)

        # notify when someone likes your comment
        response = self.user1_client.post(CREATE_LIKE_URL, {
            'content_type': 'comment',
            'object_id': comment.id,
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Notification.objects.all().count(), 2)

    def test_notify_comment_api(self):
        tweet = TestHelpers.create_tweet(self.admin)

        # notify when someone comments your tweet
        response = self.user1_client.post(CREATE_COMMENT_URL, {
            'tweet_id': tweet.id,
            'content': '1',
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Notification.objects.all().count(), 1)

    def test_unread_count_api(self):
        tweet = TestHelpers.create_tweet(self.admin)

        # anonymous is not allowed
        response = self.anonymous_client.get(UNREAD_COUNT_URL)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # POST is not allowed
        response = self.admin_client.post(UNREAD_COUNT_URL)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        # unread count is 0 by init
        response = self.admin_client.get(UNREAD_COUNT_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)

        # unread count increase when some one post comment on your tweet
        comment = TestHelpers.create_comment(self.user1, tweet)
        NotificationSerivce.send_comment_notification(comment)
        response = self.admin_client.get(UNREAD_COUNT_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

        # unread count increase when some one likes your tweet
        like = TestHelpers.create_like(self.user1, tweet)
        NotificationSerivce.send_like_notification(like)
        response = self.admin_client.get(UNREAD_COUNT_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

    def test_mark_all_as_read_api(self):
        tweet = TestHelpers.create_tweet(self.admin)
        comment = TestHelpers.create_comment(self.user1, tweet)
        like = TestHelpers.create_like(self.user1, tweet)
        NotificationSerivce.send_comment_notification(comment)
        NotificationSerivce.send_like_notification(like)

        # unread count is 2 by init
        response = self.admin_client.get(UNREAD_COUNT_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

        # anonymous is not allowed
        response = self.anonymous_client.post(MARK_ALL_AS_READ_URL)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # GET is not allowed
        response = self.admin_client.get(MARK_ALL_AS_READ_URL)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        # after mark all as read
        response = self.admin_client.post(MARK_ALL_AS_READ_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        self.assertEqual(Notification.objects.all().count(), 2)

        # unread count is 0
        response = self.admin_client.get(UNREAD_COUNT_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)

    def test_update_api(self):
        tweet = TestHelpers.create_tweet(self.admin)
        comment = TestHelpers.create_comment(self.user1, tweet)
        NotificationSerivce.send_comment_notification(comment)
        notification = Notification.objects.filter(recipient=self.admin).first()
        url = UPDATE_NOTIFICATION_URL.format(notification.id)

        # anonymous is not allowed
        response = self.anonymous_client.put(url, {'unread': False})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # GET is not allowed
        response = self.admin_client.get(url, {'unread': False})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        # set to read
        response = self.admin_client.put(url, {'unread': False})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.admin_client.get(UNREAD_COUNT_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)

        # set to unread
        response = self.admin_client.put(url, {'unread': True})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.admin_client.get(UNREAD_COUNT_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
