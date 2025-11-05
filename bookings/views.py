# bookings/apis.py
from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import *
from .serializers import *
from users.permissions import IsAdminRole
from properties.permission import IsOwner 
from django.utils import timezone
from .permissions import IsPropertyOwnerOfBooking
from django.utils import timezone
from datetime import datetime
from dateutil.relativedelta import relativedelta
from django.db.models import Count
from django.db.models.functions import TruncMonth

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



class VendorManageBookingView(generics.UpdateAPIView):
    """
    Vendor ke liye: Apni property ki booking ko 'Confirm' ya 'Cancel' karna.
    """
    queryset = Booking.objects.all()
    serializer_class = VendorBookingUpdateSerializer
    permission_classes = [permissions.IsAuthenticated, IsPropertyOwnerOfBooking]
    lookup_field = 'id' # Booking ID se


class AdminManageBookingView(generics.UpdateAPIView):
    """
    Admin ke liye: Kisi bhi booking ka status update karna.
    """
    queryset = Booking.objects.all()
    serializer_class = AdminBookingUpdateSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminRole]
    lookup_field = 'id'

class AdminBookingReportView(APIView):
    """
    For generating booking report for admin
    """

    permission_classes = [permissions.IsAuthenticated, IsAdminRole]

    def get(self, request, *args, **kwargs):
        try:
            end_date = datetime.strptime(
                request.query_params.get('end_date'), '%Y-%m-%d'
            ).date()
        except (ValueError, TypeError):
            end_date = timezone.now().date()

        try:
            start_date = datetime.strptime(
                request.query_params.get('start_date'), '%Y-%m-%d'
            ).date()
        except (ValueError, TypeError):
            start_date = end_date - relativedelta(days=30)

        # ✅ Convert to timezone-aware datetimes for production safety
        start_datetime = timezone.make_aware(datetime.combine(start_date, datetime.min.time()))
        end_datetime = timezone.make_aware(datetime.combine(end_date, datetime.max.time()))

        # ✅ Filter bookings within timezone-aware range
        bookings_in_range = Booking.objects.filter(
            booked_at__range=[start_datetime, end_datetime]
        )

        total_bookings = bookings_in_range.count()

        # ✅ Monthly aggregation (works with timezone)
        chart_data = (
            bookings_in_range
            .annotate(month=TruncMonth('booked_at'))
            .values('month')
            .annotate(count=Count('id'))
            .order_by('month')
        )

        bookings_over_time = [
            {
                'month': item['month'].strftime('%Y-%m'),
                'count': item['count']
            }
            for item in chart_data
        ]

        # ✅ Match your serializer fields
        data = {
            'total_booking_in_range': total_bookings,
            'booking_over_time': bookings_over_time
        }

        serializer = BookingReportSerializer(instance=data)
        return Response(serializer.data)
