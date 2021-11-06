from accounts.api.serializers import UserSerializer, UserSerializerWithProfile
from friendships.models import Friendship
from rest_framework import serializers
from rest_framework.validators import ValidationError
from friendships.services import FriendshipService
from accounts.services import UserService


class FriendshipSerializer(serializers.Serializer):
    from_user = serializers.SerializerMethodField()
    to_user = serializers.SerializerMethodField()
    created_at = serializers.SerializerMethodField()
    followed_from_user = serializers.SerializerMethodField()
    followed_to_user = serializers.SerializerMethodField()

    def get_from_user(self, obj):
        user = UserService.get_user_in_memcached(obj.from_user_id)
        return UserSerializer(user).data

    def get_to_user(self, obj):
        user = UserService.get_user_in_memcached(obj.to_user_id)
        return UserSerializer(user).data

    def get_created_at(self, obj):
        return obj.created_at

    def get_followed_from_user(self, obj):
        if self.context['user'].is_anonymous:
            return False
        return FriendshipService.has_followed(
            from_user_id=self.context['user'].id,
            to_user_id=obj.from_user_id,
        )

    def get_followed_to_user(self, obj):
        if self.context['user'].is_anonymous:
            return False
        return FriendshipService.has_followed(
            from_user_id=self.context['user'].id,
            to_user_id=obj.to_user_id,
        )

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class FriendshipForCreateSerializer(serializers.ModelSerializer):
    from_user_id = serializers.IntegerField()
    to_user_id = serializers.IntegerField()

    class Meta:
        model = Friendship
        fields = ('from_user_id', 'to_user_id')

    def validate(self, data):
        if data['from_user_id'] == data['to_user_id']:
            raise ValidationError({
                'message': 'user cannot follow himself',
            })
        return data

    def create(self, validated_data):
        from_user_id = validated_data['from_user_id']
        to_user_id = validated_data['to_user_id']
        return FriendshipService.follow(from_user_id=from_user_id, to_user_id=to_user_id)
