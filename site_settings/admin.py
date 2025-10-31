from django.contrib import admin
from .models import SiteSettings

@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'notify_new_user', 'notify_new_booking', 'notify_new_vendor')

    # Yeh function admin ko naya settings object banane se rokega
    # Hum chahte hain ki sirf 1 hi setting object ho
    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()