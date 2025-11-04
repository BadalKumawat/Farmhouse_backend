from django.contrib import admin
from .models import Booking

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    # एडमिन लिस्ट में ये कॉलम दिखाएँ
    list_display = (
        'id', 
        'property', 
        'user', 
        'check_in_date', 
        'check_out_date', 
        'status', 
        'total_price'
    )
    
    # For Filter
    list_filter = ('status', 'payment_method', 'check_in_date')
    
    # In search bar using user email and title)
    search_fields = ('property__title', 'user__email')
    readonly_fields = ('booked_at', 'price_per_night', 'cleaning_fee', 'service_fee', 'total_price', 'total_nights')