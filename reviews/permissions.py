from rest_framework import permissions
from bookings.models import Booking 

class HasCompletedBooking(permissions.BasePermission):
    """
    Permission to only allow users who have a 'completed' booking 
    for the property to post a review.
    """

    def has_object_permission(self, request, view, obj):
        # 'obj' yahaan 'Property' model hai

        # Check karein ki user login hai
        if not request.user.is_authenticated:
            return False

        # Check karein ki kya user ki koi 'completed' booking hai
        # is property (obj) ke liye
        return Booking.objects.filter(
            user=request.user, 
            property=obj, 
            status=Booking.BookingStatus.COMPLETED
        ).exists()