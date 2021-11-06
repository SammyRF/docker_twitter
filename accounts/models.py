from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import pre_delete, post_save
from utils.memcached.memcached_helper import invalidate_object_in_memcached

# models
class UserProfile(models.Model):
    avatar = models.FileField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    nickname = models.CharField(max_length=100, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f'{self.user}: {self.nickname}'

def get_profile(user):
    from accounts.services import UserService

    if hasattr(user, '_cached_user_profile'):
        return getattr(user, '_cached_user_profile')
    user_profile = UserService.get_userprofile_in_memcached(user.id)
    setattr(user, '_cached_user_profile', user_profile)
    return user_profile

User.profile = property(get_profile)

# listeners
def invalidate_userprofile_in_memcached(sender, instance, **kwargs):
    from accounts.services import UserService
    UserService.invalidate_userprofile_in_memcached(instance.user_id)

# memcached
post_save.connect(invalidate_object_in_memcached, sender=User)
pre_delete.connect(invalidate_object_in_memcached, sender=User)
post_save.connect(invalidate_userprofile_in_memcached, sender=UserProfile)
pre_delete.connect(invalidate_userprofile_in_memcached, sender=UserProfile)
