from accounts.api.serializers import UserSerializerWithProfile
from comments.models import Comment
from django.contrib.auth.models import User
from inbox.services import NotificationSerivce
from likes.services import LikeServices
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from tweets.models import Tweet


class CommentSerializer(serializers.ModelSerializer):
    user = UserSerializerWithProfile(source='cached_user')
    has_like = serializers.SerializerMethodField()
    likes_count = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ('id', 'user', 'tweet_id', 'content', 'created_at', 'has_like', 'likes_count')

    def get_has_like(self, obj):
        return LikeServices.has_liked(self.context['user'], obj)

    def get_likes_count(self, obj):
        return obj.like_set.count()


class CommentSerializerForCreate(serializers.ModelSerializer):
    user_id = serializers.IntegerField()
    tweet_id = serializers.IntegerField()

    class Meta:
        model = Comment
        fields = ('user_id', 'tweet_id', 'content')

    def validate(self, data):
        user_id = data['user_id']
        tweet_id = data['tweet_id']
        if not User.objects.filter(id=user_id).exists():
            raise ValidationError({
                'message': 'user not exists.'
            })
        if not Tweet.objects.filter(id=tweet_id).exists():
            raise ValidationError({
                'message': 'tweet not exists.'
            })
        return data

    def create(self, validated_data):
        comment = Comment.objects.create(
            user_id=validated_data['user_id'],
            tweet_id=validated_data['tweet_id'],
            content=validated_data['content'],
        )
        NotificationSerivce.send_comment_notification(comment)
        return comment


class CommentSerializerForUpdate(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ('content',)

    def update(self, instance, validated_data):
        instance.content = validated_data['content']
        instance.save()
        return instance
