from django.contrib import admin
from .models import Property, Amenity, PropertyImage, BlackoutDate

class PropertyAdmin(admin.ModelAdmin):
    # यह 'amenities' फील्ड को एक अच्छे "चुनें" वाले (checkbox) बॉक्स में बदल देगा
    filter_horizontal = ('amenities',)
    list_display = ('title', 'owner', 'property_type', 'city', 'base_price')
    list_filter = ('property_type', 'city', 'state')
    search_fields = ('title', 'owner__username')

# ... बाकी मॉडल को वैसे ही रजिस्टर करें
admin.site.register(Property, PropertyAdmin) # Property को नए क्लास के साथ
admin.site.register(Amenity)
admin.site.register(PropertyImage)
admin.site.register(BlackoutDate)