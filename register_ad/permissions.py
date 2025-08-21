from rest_framework.permissions import BasePermission
from .models import register_ad


class IsOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        user_id = request.user.id
        register_ad_id = register_ad.objects.filter(user_id=user_id).first()
        if request.user and request.user.is_authenticated and register_ad_id:
            return True
