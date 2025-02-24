from rest_framework.permissions import BasePermission


class IsTokenAuthenticated(BasePermission):

    def has_permission(self, request, view):
        return True if request.method == 'OPTIONS' else request.auth is not None


class IsStaff(BasePermission):

    def has_permission(self, request, view):
        return True if request.method == 'OPTIONS' else 'staff' in request.auth.cached_auth['scopes']


class IsAdminForDelete(BasePermission):

    def has_permission(self, request, view):
        if request.method == 'DELETE' and 'admin' not in request.auth.cached_auth['scopes']:
            return False

        return True