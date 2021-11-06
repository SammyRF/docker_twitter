import sys

print(__name__ + ' loaded.')

# https://docs.djangoproject.com/en/3.1/topics/cache/
# sudo apt-get install memcached
# use pip install python-memcached
# DO NOT pip install memcached or django-memcached
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': 'memcached',
        'TIMEOUT': 86400,
        'KEY_PREFIX': 'testing' if ((" ".join(sys.argv)).find('manage.py test') != -1) else ''
    },
}
