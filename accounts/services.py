from accounts.models import UserProfile
from django.contrib.auth.models import User
from utils.memcached.memcached_helper import USER_PROFILE_PATTERN, project_memcached, MemcachedHelper


class UserService:

    @classmethod
    def get_user_in_memcached(cls, user_id):
        return MemcachedHelper.get_object_in_memcached(User, user_id)

    @classmethod
    def get_userprofile_in_memcached(cls, user_id):
        key = USER_PROFILE_PATTERN.format(user_id=user_id)

        # get userprofile from cache first
        userprofile = project_memcached.get(key)
        if userprofile:
            return userprofile

        # if not found in cache, go to sql
        userprofile, _ = UserProfile.objects.get_or_create(user_id=user_id)
        project_memcached.set(key, userprofile)
        return userprofile

    @classmethod
    def invalidate_userprofile_in_memcached(cls, user_id):
        key = USER_PROFILE_PATTERN.format(user_id=user_id)
        project_memcached.delete(key)

