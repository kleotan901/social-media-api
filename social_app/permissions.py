from rest_framework.permissions import (
    SAFE_METHODS,
    BasePermission
)


class IsOwnerOrIfAuthenticatedReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        if (
                request.method in SAFE_METHODS
                and request.user
                and request.user.is_authenticated
        ):
            return True

        return obj.owner == request.user
