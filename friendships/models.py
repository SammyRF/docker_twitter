from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import pre_delete, post_save


# models
class Friendship(models.Model):
    from_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="from_user_set")
    to_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="to_user_set")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        index_together = (('from_user_id', 'created_at'), ('to_user_id', 'created_at'))
        unique_together = (('from_user_id', 'to_user_id'), )
        ordering = ('-created_at',)

    def __str__(self):
        return f'{self.from_user.id} follows {self.to_user.id}'

# listeners
def invalidate_to_users_in_memcached(sender, instance, **kwargs):
    from friendships.services import FriendshipService
    FriendshipService.invalidate_to_users_in_memcached(instance.from_user_id)

# memcached
# pre_delete.connect(invalidate_to_users_in_memcached, sender=Friendship)
# post_save.connect(invalidate_to_users_in_memcached, sender=Friendship)