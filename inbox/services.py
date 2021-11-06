from django.contrib.contenttypes.models import ContentType
from comments.models import Comment
from tweets.models import Tweet
from notifications.signals import notify


class NotificationSerivce:
    @classmethod
    def send_like_notification(cls, like):
        target = like.content_object
        # no notification when user likes on self
        if target.user == like.user:
            return
        if like.content_type == ContentType.objects.get_for_model(Comment):
            notify.send(
                sender=like.user,
                recipient=target.user,
                verb='liked your tweet',
                target=target,
            )
        elif like.content_type == ContentType.objects.get_for_model(Tweet):
            notify.send(
                sender=like.user,
                recipient=target.user,
                verb='liked your comment',
                target=target,
            )

    @classmethod
    def send_comment_notification(cls, comment):
        target = comment.tweet
        # no notification when user comments on self
        if comment.user == target.user:
            return
        notify.send(
            sender=comment.user,
            recipient=target.user,
            verb='commented your tweet',
            target=target,
        )
        