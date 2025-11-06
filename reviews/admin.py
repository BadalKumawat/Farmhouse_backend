from django.contrib import admin
from .models import *
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('id', 'property', 'user', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('property__title', 'user__username', 'comment')
    
    # Makes 'created_at' read-only in the admin
    readonly_fields = ('created_at',)

admin.site.register(Review, ReviewAdmin)


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'subject', 'is_read', 'created_at')
    list_filter = ('subject', 'is_read', 'created_at')
    search_fields = ('full_name', 'email', 'message')
    readonly_fields = ('created_at',)
    actions = ['mark_as_read']

    def mark_as_read(self, request, queryset):
        queryset.update(is_read=True)
    mark_as_read.short_description = "Mark selected messages as read"


@admin.register(VideoTestimonial)
class VideoTestimonialAdmin(admin.ModelAdmin):
    list_display = ('user', 'property', 'rating', 'is_approved', 'created_at')
    list_filter = ('is_approved', 'rating')
    search_fields = ('user__email', 'property__title')
    readonly_fields = ('user', 'property', 'created_at')
    
    # Action to manually approve testimonials
    actions = ['approve_testimonials']

    def approve_testimonials(self, request, queryset):
        queryset.update(is_approved=True)
    approve_testimonials.short_description = "Approve selected testimonials"