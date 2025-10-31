from django.contrib import admin
from .models import *

class PropertyAdmin(admin.ModelAdmin):
    filter_horizontal = ('amenities',)
    list_display = ('title', 'owner', 'property_type', 'city', 'base_price')
    list_filter = ('property_type', 'city', 'state')
    search_fields = ('title', 'owner__username')

admin.site.register(Category)
admin.site.register(Property, PropertyAdmin) # Property को नए क्लास के साथ
admin.site.register(Amenity)
admin.site.register(PropertyImage)
admin.site.register(BlackoutDate)