from django.test import TestCase
from utils.test_helpers import TestHelpers
from accounts.models import UserProfile


class UserProfileTests(TestCase):
    def setUp(self):
        TestHelpers.clear_cache()

    def test_user_profile(self):
        self.assertEqual(UserProfile.objects.all().count(), 0)
        admin = TestHelpers.create_user()
        admin_profile = admin.profile
        self.assertTrue(isinstance(admin_profile, UserProfile))
        self.assertEqual(UserProfile.objects.all().count(), 1)
