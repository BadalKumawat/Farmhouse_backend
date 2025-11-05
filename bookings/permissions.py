from rest_framework import permissions

class IsPropertyOwnerOfBooking(permissions.BasePermission):
    """
    Permission to only allow property owners to manage a booking.
    """

    def has_object_permission(self, request, view, obj):
        return obj.property.owner == request.user