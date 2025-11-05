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

# --- Vendor Revenue API ---
# payments/apis.py

# ... (baaki imports) ...
from django.db.models import Sum

# ... (MyPaymentListView ke neeche) ...

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