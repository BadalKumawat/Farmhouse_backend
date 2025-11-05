# payments/serializers.py

from rest_framework import serializers
from .models import Payment
from users.serializers import UserProfileSerializer

class MyPaymentListSerializer(serializers.ModelSerializer):
    """
    Serializer for Guest's payment history (/dashboard/payments)
    """
    # Hum booking se property ka title lenge
    property_title = serializers.CharField(source='booking.property.title', read_only=True)

    class Meta:
        model = Payment
        fields = ['id', 'transaction_id', 'property_title', 'amount', 'status', 'created_at']

class AdminPaymentListSerializer(MyPaymentListSerializer):
    """
    Serializer for Admin's payment history (/admin/dashboard/payments)
    """
    # Admin ko user ki detail bhi chahiye
    user = UserProfileSerializer(source='booking.user', read_only=True)

    class Meta(MyPaymentListSerializer.Meta):
        fields = MyPaymentListSerializer.Meta.fields + ['user']

class VendorRevenueSerializer(serializers.Serializer):
    """
    Serializer for Vendor's revenue dashboard (/vendor/dashboard/revenue)
    """
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    this_month_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    # (Payout History ke liye alag model/serializer banega)

class RevenueReportSerializer(serializers.Serializer):
    """
    Serializer for Admin's 'Revenue Report'
    """
    total_revenue_in_range = serializers.DecimalField(max_digits=12, decimal_places=2)
    revenue_over_time = serializers.ListField(child=serializers.DictField())

class AdminDashboardStatsSerializer(serializers.Serializer):
    """
    Serializer for the main admin dashboard stats (image_5450cb.png).
    """
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_users = serializers.IntegerField()
    total_properties = serializers.IntegerField()
    total_bookings = serializers.IntegerField()
    
    # Chart Data (e.g., last 6 months revenue)
    # Note: Hum is list ko yahaan define kar rahe hain, iski calculation API mein hogi
    revenue_over_time = serializers.ListField(child=serializers.DictField())