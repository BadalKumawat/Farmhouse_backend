from django.conf import settings
from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Payment
from bookings.models import Booking
from .serializers import MyPaymentListSerializer, AdminPaymentListSerializer, VendorRevenueSerializer, RevenueReportSerializer
from users.permissions import IsAdminRole
from properties.permission import IsVendor
from django.db.models import Sum
from django.utils import timezone
from datetime import datetime
from dateutil.relativedelta import relativedelta
from django.db.models.functions import TruncMonth
from users.models import CustomUser
from properties.models import Property
from dateutil.relativedelta import relativedelta
from .serializers import AdminDashboardStatsSerializer
import razorpay


# --- Guest API ---
class MyPaymentListView(generics.ListAPIView):
    """
    Guest ke liye: Apni payment history dikhana.
    (/dashboard/payments)
    """
    serializer_class = MyPaymentListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Payment.objects.filter(booking__user=self.request.user).order_by('-created_at')

# --- Admin API ---
class AdminPaymentListView(generics.ListAPIView):
    """
    Admin ke liye: Platform ki saari payments dikhana.
    (/admin/dashboard/payments)
    """
    queryset = Payment.objects.all().order_by('-created_at')
    serializer_class = AdminPaymentListSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminRole]


class VendorRevenueView(APIView):
    """
    Vendor ke liye: Uska total revenue aur stats dikhana.
    (/vendor/dashboard/revenue)
    """
    permission_classes = [permissions.IsAuthenticated, IsVendor]

    def get(self, request, *args, **kwargs):
        user = request.user
        today = timezone.now().date()
        first_day_of_month = today.replace(day=1)
        
        # Base Queryset: Vendor ki properties se judi hui sari Payments
        # Yahaan hum Payment model se filter karenge
        base_payment_queryset = Payment.objects.filter(
            booking__property__owner=user,
            status=Payment.PaymentStatus.COMPLETED
        )

        # 1. Total Revenue
        total_revenue = base_payment_queryset.aggregate(total=Sum('amount'))['total'] or 0

        # 2. This Month's Revenue
        this_month_revenue = base_payment_queryset.filter(
            created_at__gte=first_day_of_month
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        data = {
            'total_revenue': total_revenue,
            'this_month_revenue': this_month_revenue
        }
        serializer = VendorRevenueSerializer(instance=data)
        return Response(serializer.data)

# --- Admin Revenue Report API ---
class AdminRevenueReportView(APIView):
    """
    Admin ke liye: 'Revenue Report' generate karna (date range ke sath).
    (Aapke 'reports' plan ko yahaan move kar diya hai)
    """
    permission_classes = [permissions.IsAuthenticated, IsAdminRole]

    def get(self, request, *args, **kwargs):
        try:
            end_date = datetime.strptime(request.query_params.get('end_date'), '%Y-%m-%d').date()
        except (ValueError, TypeError):
            end_date = timezone.now().date()
        try:
            start_date = datetime.strptime(request.query_params.get('start_date'), '%Y-%m-%d').date()
        except (ValueError, TypeError):
            start_date = end_date - relativedelta(days=30)

        # Base Queryset (Completed Payments)
        payments_in_range = Payment.objects.filter(
            created_at__range=[start_date, end_date],
            status=Payment.PaymentStatus.COMPLETED
        )

        # Data Calculate karein
        total_revenue = payments_in_range.aggregate(total=Sum('amount'))['total'] or 0

        # Chart Data: Revenue Over Time
        chart_data = payments_in_range.annotate(
            month=TruncMonth('created_at')
        ).values('month').annotate(
            revenue=Sum('amount')
        ).order_by('month')

        revenue_over_time = [
            {'month': item['month'].strftime('%Y-%m'), 'revenue': item['revenue']}
            for item in chart_data
        ]

        data = {
            'total_revenue_in_range': total_revenue,
            'revenue_over_time': revenue_over_time
        }
        serializer = RevenueReportSerializer(instance=data)
        return Response(serializer.data)


'''client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

#  View to Create Razorpay Order
class RazorpayOrderCreateView(APIView):
    """
    API to create a Razorpay Order ID for a given Booking ID.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        booking_id = request.data.get('booking_id')

        try:
            booking = Booking.objects.get(id=booking_id, user=request.user)
            if booking.payment_method == 'cash':
                return Response({'error': 'Payment method is Cash, no online payment needed.'}, status=status.HTTP_400_BAD_REQUEST)
            if booking.payment.status != 'pending':
                 return Response({'error': 'Payment already processed.'}, status=status.HTTP_400_BAD_REQUEST)
        except Booking.DoesNotExist:
            return Response({'error': 'Booking not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Amount ko paise mein badlein (₹100 = 10000 paise)
        amount_paise = int(booking.total_price * 100) 

        try:
            order = client.order.create({
                'amount': amount_paise,
                'currency': 'INR',
                'receipt': booking.payment.transaction_id,
                'payment_capture': '1'
            })
            
            # Payment object ko update karein
            booking.payment.razorpay_order_id = order['id']
            booking.payment.save()

            serializer = RazorpayOrderSerializer({
                'booking_id': booking.id,
                'order_id': order['id'],
                'amount': booking.total_price,
                'key_id': settings.RAZORPAY_KEY_ID
            })
            return Response(serializer.data)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# --- View to Verify Payment ---
class RazorpayVerifyPaymentView(APIView):
    """
    API to verify payment signature and update Booking/Payment status.
    """
    permission_classes = [permissions.AllowAny] # Razorpay webhook ya Frontend se call

    def post(self, request):
        serializer = RazorpayVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Verify the signature (Razorpay ki library se)
        try:
            params_dict = {
                'razorpay_order_id': serializer.validated_data['razorpay_order_id'],
                'razorpay_payment_id': serializer.validated_data['razorpay_payment_id'],
                'razorpay_signature': serializer.validated_data['razorpay_signature']
            }
            client.utility.verify_payment_signature(params_dict)

        except Exception:
            return Response({'message': 'Signature verification failed.'}, status=status.HTTP_400_BAD_REQUEST)

        # Payment aur Booking status update karein
        try:
            payment = Payment.objects.get(razorpay_order_id=serializer.validated_data['razorpay_order_id'])
            payment.razorpay_payment_id = serializer.validated_data['razorpay_payment_id']
            payment.razorpay_signature = serializer.validated_data['razorpay_signature']
            payment.status = Payment.PaymentStatus.COMPLETED
            payment.save()

            # Booking status ko CONFIRMED karein
            payment.booking.status = Booking.BookingStatus.CONFIRMED
            payment.booking.save()
            
            # Yahaan aap Guest aur Vendor ko confirmation email bhej sakte hain

            return Response({'message': 'Payment confirmed and booking is active.'}, status=status.HTTP_200_OK)

        except Payment.DoesNotExist:
            return Response({'error': 'Payment record not found.'}, status=status.HTTP_404_NOT_FOUND)
            '''

class AdminDashboardStatsView(APIView):
    """
    API for the main Admin Dashboard (image_5450cb.png).
    Provides all-time stats and revenue charts.
    """
    permission_classes = [permissions.IsAuthenticated, IsAdminRole]

    def get(self, request, *args, **kwargs):
        # --- YEH HAI FIX ---
        # Note: dateutil.relativedelta ko import karna zaroori hai
        
        # 1. All-Time Stats Cards
        total_revenue = Payment.objects.filter(status=Payment.PaymentStatus.COMPLETED).aggregate(total=Sum('amount'))['total'] or 0
        total_users = CustomUser.objects.count()
        total_properties = Property.objects.filter(status=Property.PropertyStatus.APPROVED).count()
        total_bookings = Booking.objects.count()
        
        # 2. Revenue Overview Chart (Last 6 Months)
        # 6 mahine pehle ki date
        six_months_ago = datetime.now().date() - relativedelta(months=6) 
        
        # Completed payments ko filter karein
        revenue_data = Payment.objects.filter(
            status=Payment.PaymentStatus.COMPLETED,
            created_at__gte=six_months_ago
        ).annotate(
            month=TruncMonth('created_at')
        ).values('month').annotate(
            revenue=Sum('amount')
        ).order_by('month')

        # Data ko chart ke liye format karein
        revenue_over_time = [
            {'month': item['month'].strftime('%Y-%m'), 'revenue': item['revenue']}
            for item in revenue_data
        ]
        
        # 3. Serializer ko data bhejein
        data = {
            'total_revenue': total_revenue,
            'total_users': total_users,
            'total_properties': total_properties,
            'total_bookings': total_bookings,
            'revenue_over_time': revenue_over_time
        }
        
        # Hum 'instance=' ka istemal karenge (taaki validation skip ho)
        serializer = AdminDashboardStatsSerializer(instance=data)
        return Response(serializer.data)