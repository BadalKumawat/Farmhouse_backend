# bookings/apis.py
from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import *
from .serializers import *
from users.permissions import IsAdminRole
# from properties.permissions import IsOwner 
from django.utils import timezone

# --- Guest APIs ---

class BookingCreateView(generics.CreateAPIView):
    """
    Guest ke liye: Nayi booking create karna.
    """
    serializer_class = BookingCreateSerializer
    permission_classes = [permissions.IsAuthenticated] # Sirf login user

    def get_serializer_context(self):
        # Serializer ko 'request' pass karein taaki user.id mil sake
        context = super().get_serializer_context()
        context.update({'request': self.request})
        return context

class MyBookingListView(generics.ListAPIView):
    """
    Guest ke liye: 'My Bookings' list dikhana.
    (/dashboard/bookings)
    """
    serializer_class = BookingListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        
        # Filter logic for 'Upcoming', 'Past', 'Cancelled'
        query_status = self.request.query_params.get('status', None)
        
        queryset = Booking.objects.filter(user=user).order_by('-check_in_date')
        
        today = timezone.now().date()
        
        if query_status == 'upcoming':
            return queryset.filter(status='confirmed', check_in_date__gte=today)
        elif query_status == 'past':
            return queryset.filter(status='completed', check_out_date__lt=today)
        elif query_status == 'cancelled':
            return queryset.filter(status='cancelled')
        
        return queryset # Default: Sab dikhao

class MyBookingDetailView(generics.RetrieveAPIView):
    """
    Guest ke liye: Ek booking ki poori detail.
    (/dashboard/bookings/1)
    """
    serializer_class = BookingDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'
    
    def get_queryset(self):
        # User sirf apni booking hi dekh sakta hai
        return Booking.objects.filter(user=self.request.user)

class MyBookingCancelView(APIView):
    """
    Guest ke liye: Ek 'pending' ya 'confirmed' booking ko cancel karna.
    """
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, id, *args, **kwargs):
        try:
            booking = Booking.objects.get(id=id, user=request.user)
        except Booking.DoesNotExist:
            return Response({'error': 'Booking not found.'}, status=status.HTTP_404_NOT_FOUND)
            
        if booking.status in ['completed', 'cancelled']:
            return Response({'error': 'This booking cannot be cancelled.'}, status=status.HTTP_400_BAD_REQUEST)
        
        booking.status = Booking.BookingStatus.CANCELLED
        booking.save()
        
        # (Phase 7) Yahaan Vendor ko notification bhej sakte hain
        
        return Response({'message': 'Booking cancelled successfully.'}, status=status.HTTP_200_OK)

# --- Vendor APIs ---

class VendorBookingListView(generics.ListAPIView):
    """
    Vendor ke liye: Uski properties par aayi bookings ki list.
    (/vendor/dashboard/bookings)
    """
    serializer_class = BookingListSerializer
    permission_classes = [permissions.IsAuthenticated] # (IsVendor permission bhi add kar sakte hain)

    def get_queryset(self):
        user = self.request.user
        # Sirf woh bookings jo vendor ki properties par hain
        return Booking.objects.filter(property__owner=user).order_by('-check_in_date')

# --- Admin APIs ---

class AdminBookingListView(generics.ListAPIView):
    """
    Admin ke liye: Platform ki saari bookings ki list.
    (/admin/dashboard/bookings)
    """
    queryset = Booking.objects.all().order_by('-booked_at')
    serializer_class = AdminBookingListSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminRole]