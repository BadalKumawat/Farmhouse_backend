from django.contrib import admin
from .models import Review

class ReviewAdmin(admin.ModelAdmin):
    list_display = ('id', 'property', 'user', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('property__title', 'user__username', 'comment')
    
    # Makes 'created_at' read-only in the admin
    readonly_fields = ('created_at',)

admin.site.register(Review, ReviewAdmin)