from django.test import TestCase
from inbox.services import NotificationSerivce
from notifications.models import Notification
from rest_framework.test import APIClient
from utils.test_helpers import TestHelpers


class NotificationsServiceTests(TestCase):

    def setUp(self):
        TestHelpers.clear_cache()

        self.admin = TestHelpers.create_user()
        self.admin_client = APIClient()
        self.admin_client.force_authenticate(self.admin)

        self.user1 = TestHelpers.create_user('user1')
        self.user1_client = APIClient()
        self.user1_client.force_authenticate(self.user1)

    def test_notify_like(self):
        tweet = TestHelpers.create_tweet(self.admin)
        comment = TestHelpers.create_comment(self.admin, tweet)

        # no notification when user likes on self
        like = TestHelpers.create_like(self.admin, tweet)
        NotificationSerivce.send_like_notification(like)
        self.assertEqual(Notification.objects.all().count(), 0)

        # no notification when user likes on self
        like = TestHelpers.create_like(self.admin, comment)
        NotificationSerivce.send_like_notification(like)
        self.assertEqual(Notification.objects.all().count(), 0)

        # notify when other likes tweet
        like = TestHelpers.create_like(self.user1, tweet)
        NotificationSerivce.send_like_notification(like)
        self.assertEqual(Notification.objects.all().count(), 1)
        self.assertEqual(Notification.objects.filter(recipient=self.user1).count(), 0)
        self.assertEqual(Notification.objects.filter(recipient=self.admin).count(), 1)

        # notify when other likes comment
        like = TestHelpers.create_like(self.user1, comment)
        NotificationSerivce.send_like_notification(like)
        self.assertEqual(Notification.objects.all().count(), 2)
        self.assertEqual(Notification.objects.filter(recipient=self.user1).count(), 0)
        self.assertEqual(Notification.objects.filter(recipient=self.admin).count(), 2)

    def test_notify_comment(self):
        tweet = TestHelpers.create_tweet(self.admin)

        # no notification when comments on self
        comment = TestHelpers.create_comment(self.admin, tweet)
        NotificationSerivce.send_comment_notification(comment)
        self.assertEqual(Notification.objects.all().count(), 0)

        # notify when other comments tweet
        comment = TestHelpers.create_comment(self.user1, tweet)
        NotificationSerivce.send_comment_notification(comment)
        self.assertEqual(Notification.objects.all().count(), 1)
        self.assertEqual(Notification.objects.filter(recipient=self.user1).count(), 0)
        self.assertEqual(Notification.objects.filter(recipient=self.admin).count(), 1)
