from friendships.hbase_models import HBaseFromUser, HBaseToUser
from friendships.models import Friendship
from utils.gatekeeper.models import GateKeeper
from utils.memcached.memcached_helper import TO_USERS_PATTERN, project_memcached
import time


class FriendshipService:

    @classmethod
    def get_friendships(cls, from_user_id=None, to_user_id=None):
        if not GateKeeper.is_switch_on('switch_friendship_to_hbase'):
            # get list from mysql
            if from_user_id:
                friendships = Friendship.objects.filter(from_user_id=from_user_id).order_by('-created_at')
            else:
                friendships = Friendship.objects.filter(to_user_id=to_user_id).order_by('-created_at')
        else:
            # get list from hbase
            if from_user_id:
                friendships = HBaseFromUser.filter(prefix=(from_user_id, ))
            else:
                friendships = HBaseToUser.filter(prefix=(to_user_id, ))
        return friendships

    @classmethod
    def follow(cls, from_user_id, to_user_id):
        # user cannot follow self
        if from_user_id == to_user_id:
            return None

        # invalid cached to_users in memcached when follow
        cls.invalidate_to_users_in_memcached(from_user_id)

        if not GateKeeper.is_switch_on('switch_friendship_to_hbase'):
            # create in mysql
            return Friendship.objects.create(
                from_user_id=from_user_id,
                to_user_id=to_user_id,
            )
        else:
            # create in hbase
            ts_now = int(time.time() * 1000000)
            HBaseToUser.create(
                from_user_id=from_user_id,
                to_user_id=to_user_id,
                created_at=ts_now,
            )
            return HBaseFromUser.create(
                from_user_id=from_user_id,
                to_user_id=to_user_id,
                created_at=ts_now,
            )

    @classmethod
    def unfollow(cls, from_user_id, to_user_id):
        # user cannot unfollow self
        if from_user_id == to_user_id:
            return None

        # invalid cached to_users in memcached when unfollow
        cls.invalidate_to_users_in_memcached(from_user_id)
        if not GateKeeper.is_switch_on('switch_friendship_to_hbase'):
            # remove in mysql
            deleted, _ = Friendship.objects.filter(
                from_user_id=from_user_id,
                to_user_id=to_user_id,
            ).delete()
            return deleted
        else:
            # remove in hbase
            friendships = HBaseFromUser.filter(prefix=(from_user_id,))
            for friendship in friendships:
                if friendship.to_user_id == int(to_user_id):
                    ts = friendship.created_at
                    HBaseToUser.delete(
                        to_user_id=to_user_id,
                        created_at=ts,
                    )
                    HBaseFromUser.delete(
                        from_user_id=from_user_id,
                        created_at=ts,
                    )
                    return True
            else:
                return False

    @classmethod
    def get_to_users_in_memcached(cls, from_user_id):
        key = TO_USERS_PATTERN.format(from_user_id=from_user_id)
        to_users = project_memcached.get(key)
        if to_users is not None:
            return to_users

        if not GateKeeper.is_switch_on('switch_friendship_to_hbase'):
            # get from mysql
            friendships = Friendship.objects.filter(from_user_id=from_user_id)
        else:
            # get from hbase
            friendships = HBaseFromUser.filter(prefix=(from_user_id,))
        to_users = set([
            fs.to_user_id
            for fs in friendships
        ])
        project_memcached.set(key, to_users)
        return to_users

    @classmethod
    def has_followed(cls, from_user_id, to_user_id):
        return int(to_user_id) in cls.get_to_users_in_memcached(from_user_id)

    @classmethod
    def invalidate_to_users_in_memcached(cls, from_user_id):
        key = TO_USERS_PATTERN.format(from_user_id=from_user_id)
        project_memcached.delete(key)
