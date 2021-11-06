import sys

print(__name__ + ' loaded.')

# sudo apt-get install redis
# pip install redis
REDIS_HOST = 'redis'
REDIS_PORT = 6379
REDIS_DB = 0 if ((" ".join(sys.argv)).find('manage.py test') == -1) else 1
REDIS_KEY_EXPIRE_TIME = 7 * 86400  # in seconds
REDIS_LIST_LENGTH_LIMIT = 1000 if not ((" ".join(sys.argv)).find('manage.py test') == -1) else 10
