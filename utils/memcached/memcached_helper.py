from django.conf import settings
from django.core.cache import caches


TO_USERS_PATTERN = 'to_users:{from_user_id}'
USER_PROFILE_PATTERN = 'userprofile:{user_id}'

project_memcached = caches['default']


class MemcachedHelper:
    @classmethod
    def _get_key(cls, model_class, object_id):
        return '{}:{}'.format(model_class.__name__, object_id)

    @classmethod
    def get_object_in_memcached(cls, model_class, object_id):
        key = cls._get_key(model_class, object_id)

        # cache hit
        obj = project_memcached.get(key)
        if obj:
            return obj

        # cache miss
        obj = model_class.objects.filter(id=object_id).first()
        if obj:
            project_memcached.set(key, obj)

        return obj

    @classmethod
    def invalidate_object_in_memcached(cls, model_class, object_id):
        key = cls._get_key(model_class, object_id)
        project_memcached.delete(key)


def invalidate_object_in_memcached(sender, instance, **kwargs):
    MemcachedHelper.invalidate_object_in_memcached(sender, instance.id)