from django.contrib import admin
from .models import Payment

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('transaction_id', 'booking', 'amount', 'status', 'payment_method', 'created_at')
    list_filter = ('status', 'payment_method')
    search_fields = ('transaction_id', 'booking__user__email', 'booking__property__title')
    readonly_fields = ('created_at', 'updated_at')