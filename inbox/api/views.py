from inbox.api.serializers import NotificationSerializer, NotificationSerializerForUpdate
from notifications.models import Notification
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from utils import helpers
from utils.decorators import required_all_params, rate_limit
from utils.permissions import IsObjectOwner


class NotificationViewSet(viewsets.GenericViewSet, viewsets.mixins.ListModelMixin):
    serializer_class = NotificationSerializer
    permission_classes = (IsAuthenticated, IsObjectOwner)

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)

    @action(methods=['GET'], detail=False, url_path='unread-count')
    @rate_limit(hms=(0, 6, 0))
    def unread_count(self, request):
        count = Notification.objects.filter(recipient=request.user, unread=True).count()
        return Response({
            'success': True,
            'count': count,
        }, status=status.HTTP_200_OK)

    @action(methods=['POST'], detail=False, url_path='mark-all-as-read')
    @rate_limit(hms=(0, 6, 0))
    def mark_all_as_read(self, request):
        count = Notification.objects.filter(recipient=request.user, unread=True).update(unread=False)
        return Response({
            'success': True,
            'count': count,
        }, status=status.HTTP_200_OK)

    @required_all_params(method='POST', params=('unread',))
    @rate_limit(hms=(0, 6, 0))
    def update(self, request, pk):
        serializer = NotificationSerializerForUpdate(
            instance=self.get_object(),
            data=request.data,
        )
        if not serializer.is_valid():
            return helpers.validation_errors_response(serializer.errors)

        notification = serializer.save()
        return Response(NotificationSerializer(notification).data, status=status.HTTP_200_OK)
