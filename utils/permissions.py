from notifications.models import Notification
from rest_framework.permissions import BasePermission


class IsObjectOwner(BasePermission):
    # for action with Detail=False and Detail=True
    def has_permission(self, request, view):
        return True

    # for action with Detail=True only
    def has_object_permission(self, request, view, obj):
        if isinstance(obj, Notification):
            return request.user == obj.recipient
        return request.user == obj.user
