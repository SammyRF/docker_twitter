import sys

print(__name__ + ' loaded.')

RATE_LIMIT_ENABLE = ((" ".join(sys.argv)).find('manage.py test') == -1)
RATE_LIMIT_PREFIX = 'rate-limit'
