from rest_framework import permissions

class IsVendor(permissions.BasePermission):
    """
    Custom permission to only allow users with 'vendor' role.
    """

    def has_permission(self, request, view):
        # Check karo ki user login hai, uska role 'vendor' hai,
        # aur uska status 'active' ya 'verified' hai.
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == 'vendor' and
            request.user.status in ['active', 'verified']
        )
    
class IsOwner(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit or delete it.
    """

    def has_object_permission(self, request, view, obj):
        # 'obj' yahaan 'Property' model hai
        # Check karo ki property ka owner (obj.owner)
        # wahi user hai jo request bhej raha hai (request.user)
        return obj.owner == request.user