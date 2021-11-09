from kombu import Queue
import sys

print(__name__ + ' loaded.')

# celery -A twitter worker -l INFO
# CELERY_BROKER_URL = 'redis://redis/2' if ((" ".join(sys.argv)).find('manage.py test') != -1) else 'redis://redis/0'
CELERY_BROKER_URL = 'amqp://guest@rabbitmq'
CELERY_TIMEZONE = "UTC"
CELERY_TASK_ALWAYS_EAGER = ((" ".join(sys.argv)).find('manage.py test') != -1)
CELERY_QUEUES = (
    Queue('default', routing_key='default'),
    Queue('newsfeeds', routing_key='newsfeeds'),
)
