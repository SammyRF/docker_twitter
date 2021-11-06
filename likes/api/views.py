from likes.api.serializers import LikeSerializerForCreate, LikeSerializer, LikeSerializerForCancel
from likes.models import Like
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from utils import helpers
from utils.decorators import required_all_params, rate_limit


class LikeViewSet(viewsets.GenericViewSet):
    queryset = Like.objects.all()
    serializer_class = LikeSerializerForCreate
    permission_classes = [IsAuthenticated]

    @required_all_params(method='POST', params=('content_type', 'object_id'))
    @rate_limit(hms=(0, 6, 0))
    def create(self, request):
        serializer = LikeSerializerForCreate(
            data=request.data,
            context={'user': request.user},
        )

        if not serializer.is_valid():
            return helpers.validation_errors_response(serializer.errors)

        like = serializer.save()
        return Response(LikeSerializer(like).data, status=status.HTTP_201_CREATED)

    @action(methods=['POST'], detail=False)
    @required_all_params(method='POST', params=('content_type', 'object_id'))
    @rate_limit(hms=(0, 6, 0))
    def cancel(self, request):
        serializer = LikeSerializerForCancel(
            data=request.data,
            context={'user': request.user},
        )

        if not serializer.is_valid():
            return helpers.validation_errors_response(serializer.errors)

        cnt, _ = serializer.cancel()
        if cnt > 0:
            return Response({
                'success': True,
                'message': 'Like cancelled',
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'message': 'Like was not created by the user',
            }, status=status.HTTP_403_FORBIDDEN)

