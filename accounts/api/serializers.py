from accounts.models import UserProfile
from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework.exceptions import ValidationError


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username')


class UserSerializerWithProfile(serializers.ModelSerializer):
    nickname = serializers.CharField(source='profile.nickname')
    avatar_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'username', 'nickname', 'avatar_url')

    def get_avatar_url(self, obj):
        if obj.profile.avatar:
            return obj.profile.avatar.url
        return None


class UserSerializerForSignup(serializers.Serializer):
    username = serializers.CharField(max_length=20, min_length=5)
    password = serializers.CharField(max_length=20, min_length=5)
    email = serializers.EmailField()

    class Meta:
        model = User
        fields = ('username', 'password', 'email')

    def validate(self, data):
        username = data['username'].lower()
        password = data['password']
        email = data['email'].lower()
        if User.objects.filter(username=username).exists() \
            or User.objects.filter(email=email).exists():
            raise ValidationError({
                'message': 'This email address has been occupied.'
            })
        data['username'] = username
        data['password'] = password
        data['email'] = email
        return data

    def create(self, validated_data):
        username = validated_data['username']
        password = validated_data['password']
        email = validated_data['email']
        user = User.objects.create_user(username=username, password=password, email=email)
        user.profile
        return user


class UserSerializerForLogin(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()


class UserProfileSerializerForUpdate(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ('id', 'nickname', 'avatar')