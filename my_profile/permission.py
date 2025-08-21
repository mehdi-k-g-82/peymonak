from rest_framework.permissions import BasePermission

class DenyProfileDeletion(BasePermission):
    def has_permission(self, request, view):
        if request.method == 'DELETE' and view.action == 'destroy':
            return False
        return True