from celery import shared_task
from django.conf import settings
from friendships.services import FriendshipService
from newsfeeds.models import NewsFeed

FANOUT_TIME_LIMIT = 3600 # 1hour
FANOUT_BATCH_SIZE = 1000 if not settings.TESTING else 3


@shared_task(routing_key='default', time_limit=FANOUT_TIME_LIMIT)
def fan_out_main_task(tweet_id, tweet_user_id, created_at):
    from newsfeeds.services import NewsFeedService
    # add user self first, make sure that user can see it in his own newsfeed fast
    NewsFeedService.create(user_id=tweet_user_id, tweet_id=tweet_id, created_at=created_at)

    friendships = FriendshipService.get_friendships(to_user_id=tweet_user_id)
    from_user_ids = [friendship.from_user_id for friendship in friendships]
    idx = 0
    while idx < len(from_user_ids):
        batch_ids = from_user_ids[idx : idx + FANOUT_BATCH_SIZE]
        fan_out_batch_task.delay(tweet_id, batch_ids, created_at)
        idx += FANOUT_BATCH_SIZE

    size = len(from_user_ids)
    return f'{size} newsfeeds fan out with {(size - 1) // FANOUT_BATCH_SIZE + 1} batches.'


@shared_task(routing_key='newsfeeds', time_limit=FANOUT_TIME_LIMIT)
def fan_out_batch_task(tweet_id, from_user_ids, created_at):
    from newsfeeds.services import NewsFeedService
    newsfeeds_data = [
        {'user_id': from_user_id, 'tweet_id': tweet_id, 'created_at': created_at}
        for from_user_id in from_user_ids
    ]
    # bulk_create improved performance
    NewsFeedService.bulk_create(newsfeeds_data)
    return f'{len(newsfeeds_data)} newsfeeds are created.'

