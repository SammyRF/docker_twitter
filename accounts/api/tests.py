from accounts.models import UserProfile
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from utils.test_helpers import TestHelpers

BASE_ACCOUNTS_URL = '/api/accounts/{}/'
LOGIN_URL = BASE_ACCOUNTS_URL.format('login')
LOGOUT_URL = BASE_ACCOUNTS_URL.format('logout')
SIGNUP_URL = BASE_ACCOUNTS_URL.format('signup')
SIGNOFF_URL = BASE_ACCOUNTS_URL.format('signoff')
LOGIN_STATUS_URL = BASE_ACCOUNTS_URL.format('login_status')

USER_PROFILE_URL = '/api/profiles/{}/'

class AccountsApiTests(TestCase):
    def setUp(self):
        TestHelpers.clear_cache()

        self.client = APIClient()
        self.user = TestHelpers.create_user()

    def test_login_api(self):
        # test GET not allowed
        response = self.client.get(LOGIN_URL, {
            'username': self.user.username,
            'password': 'correct password',
        })
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        # test with 'wrong password'
        response = self.client.post(LOGIN_URL, {
            'username': self.user.username,
            'password': 'wrong password',
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # test failed login status
        response = self.client.get(LOGIN_STATUS_URL)
        self.assertFalse(response.data['has_logged_in'])

        # test with 'correct password'
        response = self.client.post(LOGIN_URL, {
            'username': self.user.username,
            'password': 'correct password',
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(response.data['user'])
        self.assertEqual(response.data['user']['id'], self.user.id)

        # test success login status
        response = self.client.get(LOGIN_STATUS_URL)
        self.assertTrue(response.data['has_logged_in'])

    def test_logout_api(self):
        # login first
        self.client.post(LOGIN_URL, {
            'username': self.user.username,
            'password': 'correct password',
        })

        # test login status
        response = self.client.get(LOGIN_STATUS_URL)
        self.assertTrue(response.data['has_logged_in'])

        # test logout with 'GET'
        response = self.client.get(LOGOUT_URL)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        # test logout
        response = self.client.post(LOGOUT_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # test login status
        response = self.client.get(LOGIN_STATUS_URL)
        self.assertFalse(response.data['has_logged_in'])

    def test_signup_api(self):
        # test sign up with 'GET'
        response = self.client.get(SIGNUP_URL, {
            'username': 'guest',
            'password': 'guest',
            'email': 'guest@guest.com',
        })
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        # test wrong email
        response = self.client.post(SIGNUP_URL, {
            'username': 'guest',
            'password': 'guest',
            'email': 'wrong email',
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # test too short password
        response = self.client.post(SIGNUP_URL, {
            'username': 'guest',
            'password': 'pwd',
            'email': 'guest@guest.com',
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # test too long username
        response = self.client.post(SIGNUP_URL, {
            'username': 'user name is too long',
            'password': 'guest',
            'email': 'guest@guest.com',
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # sign up
        response = self.client.post(SIGNUP_URL, {
            'username': 'guest',
            'password': 'guest',
            'email': 'guest@guest.com',
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user_id = response.data['user']['id']
        self.assertEqual(UserProfile.objects.filter(user=user_id).count(), 1)

        # test login status
        response = self.client.get(LOGIN_STATUS_URL)
        self.assertTrue(response.data['has_logged_in'])

    def test_signoff_api(self):
        # test sign off with 'GET'
        response = self.client.get(SIGNOFF_URL, {
            'username': 'guest',
            'password': 'guest',
        })
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        # sign up
        response = self.client.post(SIGNUP_URL, {
            'username': 'guest',
            'password': 'guest',
            'email': 'guest@guest.com',
        })
        self.assertTrue(User.objects.filter(username='guest').exists())

        # sign off
        response = self.client.post(SIGNOFF_URL, {
            'username': 'guest',
            'password': 'guest',
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(User.objects.filter(username='guest').exists())

        # sign off 'admin' is not allowed
        response = self.client.post(SIGNOFF_URL, {
            'username': 'admin',
            'password': 'admin',
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class UserProfileApiTests(TestCase):
    def setUp(self):
        self.anonymous_client = APIClient()

        self.admin = TestHelpers.create_user()
        self.admin_client = APIClient()
        self.admin_client.force_authenticate(self.admin)
        self.user1 = TestHelpers.create_user('user1')
        self.user1_client = APIClient()
        self.user1_client.force_authenticate(self.user1)

        # create profile
        self.profile = TestHelpers.create_profile(self.admin)

    def test_retieve_api(self):
        url = USER_PROFILE_URL.format(self.profile.id)

        # test anonymous not allowed
        response = self.anonymous_client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # test 'other user' not allowed
        response = self.user1_client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # normal case
        response = self.admin_client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['nickname'], 'Sam')

    def test_update_api(self):
        url = USER_PROFILE_URL.format(self.profile.id)

        # test anonymous not allowed
        response = self.anonymous_client.put(url, {'nickname': 'Xiao'})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # test 'other user' not allowed
        response = self.user1_client.put(url, {'nickname': 'Xiao'})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # normal case for nickname
        response = self.admin_client.put(url, {'nickname': 'Xiao'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['nickname'], 'Xiao')

        # normal case for avatar
        response = self.admin_client.put(url, {
            'avatar': SimpleUploadedFile(
                name='test_avatar.jpg',
                content=str.encode('a fake avatar'),
                content_type='image/jpeg',
            )
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue('test_avatar' in response.data['avatar'])
        self.profile.refresh_from_db()
        self.assertIsNotNone(self.profile.avatar)