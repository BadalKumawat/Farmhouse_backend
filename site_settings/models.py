from django.db import models

class SiteSettings(models.Model):
    notify_new_user = models.BooleanField(default=True, verbose_name="New User Registration")
    notify_new_booking = models.BooleanField(default=True, verbose_name="New Booking")
    notify_new_vendor = models.BooleanField(default=True, verbose_name="New Vendor Application")
    # Aap yahaan 'Site Name' aur 'Support Email' bhi daal sakte hain

    class Meta:
        verbose_name_plural = "Site Settings"

    def __str__(self):
        return "Site Notification Settings"