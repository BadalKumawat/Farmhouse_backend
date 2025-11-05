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