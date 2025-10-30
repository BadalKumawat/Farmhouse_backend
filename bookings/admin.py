from django.contrib import admin
from .models import Booking

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
    
    # राइट साइडबार में फ़िल्टर
    list_filter = ('status', 'payment_method', 'check_in_date')
    
    # सर्च बार (प्रॉपर्टी के टाइटल या यूज़र के नाम से)
    search_fields = ('property__title', 'user__username')

# मॉडल को रजिस्टर करें
admin.site.register(Booking, BookingAdmin)