from friendships.api.serializers import FriendshipSerializer, FriendshipForCreateSerializer
from friendships.models import Friendship
from friendships.services import FriendshipService
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from utils import helpers
from utils.decorators import required_all_params, required_any_params, rate_limit
from utils.gatekeeper.models import GateKeeper
from utils.paginations import EndlessPagination
from friendships.hbase_models import HBaseFromUser, HBaseToUser


class FriendshipViewSet(viewsets.GenericViewSet):
    serializer_class = FriendshipForCreateSerializer
    pagination_class = EndlessPagination

    @required_any_params(method='GET', params=('from_user_id', 'to_user_id'))
    @rate_limit(hms=(0, 6, 0))
    def list(self, request):
        from_user_id = request.query_params.get('from_user_id')
        to_user_id = request.query_params.get('to_user_id')
        if not GateKeeper.is_switch_on('switch_friendship_to_hbase'):
            # pagination in mysql
            if from_user_id:
                friendships = Friendship.objects.filter(from_user_id=from_user_id).order_by('-created_at')
            else:
                friendships = Friendship.objects.filter(to_user_id=to_user_id).order_by('-created_at')
            page = self.paginate_queryset(friendships)
        else:
            # pagination in hbase
            if from_user_id:
                page = self.paginator.paginate_hbase(HBaseFromUser, (from_user_id, ), request)
            else:
                page = self.paginator.paginate_hbase(HBaseToUser, (to_user_id,), request)
        serializer = FriendshipSerializer(page, context={'user': request.user}, many=True)
        return self.paginator.get_paginated_response(serializer.data)

    @action(methods=['POST'], detail=False, permission_classes=[IsAuthenticated,])
    @required_all_params(method='POST', params=('user_id',))
    @rate_limit(hms=(0, 6, 0))
    def follow(self, request):
        to_user_id = request.data.get('user_id')

        # if friendship exists, skip
        if FriendshipService.has_followed(from_user_id=request.user.id, to_user_id=to_user_id):
            return Response({
                'success': True,
                'message': 'friendship exists',
            }, status=status.HTTP_200_OK)

        serializer = FriendshipForCreateSerializer(data={
            'from_user_id': request.user.id,
            'to_user_id': to_user_id,
        })

        if not serializer.is_valid():
            return helpers.validation_errors_response(serializer.errors)

        friendship = serializer.save()
        return Response({
            'friendships': FriendshipSerializer(friendship, context={'user': request.user}).data,
        }, status=status.HTTP_201_CREATED)

    @action(methods=['POST'], detail=False, permission_classes=[IsAuthenticated])
    @required_all_params(method='POST', params=('user_id',))
    @rate_limit(hms=(0, 6, 0))
    def unfollow(self, request):
        to_user_id = request.data.get('user_id')
        if str(request.user.id) == to_user_id:
            return Response({
                'success': False,
                'message': 'user cannot unfollow himself',
            }, status=status.HTTP_400_BAD_REQUEST)

        if not FriendshipService.has_followed(from_user_id=request.user.id, to_user_id=to_user_id):
            return Response({
                'success': False,
                'message': 'friendship not found',
            }, status=status.HTTP_400_BAD_REQUEST)

        FriendshipService.unfollow(from_user_id=request.user.id, to_user_id=to_user_id)
        return Response({
            'success': True,
            'message': 'friendship deleted'
        }, status=status.HTTP_200_OK)




