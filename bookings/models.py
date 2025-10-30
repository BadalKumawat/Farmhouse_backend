from django.db import models
from django.conf import settings # For CustomUser
from properties.models import Property # To link to the Property model

class Booking(models.Model):

    # --- Booking Status Choices ---
    class BookingStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'       # Initial status
        CONFIRMED = 'confirmed', 'Confirmed' # After payment or vendor approval
        CANCELLED = 'cancelled', 'Cancelled'   # If user or vendor cancels
        COMPLETED = 'completed', 'Completed'   # After check-out

    # --- Payment Method Choices ---
    class PaymentMethod(models.TextChoices):
        ONLINE = 'online', 'Online'
        AT_PROPERTY = 'cash', 'Cash'

    # --- Core Booking Details ---
    # Link to the user who is booking (must be a 'guest')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bookings',
        limit_choices_to={'role': 'guest'}
    )
    
    # Link to the property being booked
    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name='bookings'
    )

    # --- Your Requested Fields ---
    check_in_date = models.DateField()
    check_out_date = models.DateField()
    guests_count = models.PositiveIntegerField(verbose_name="Number of Guests")
    payment_method = models.CharField(
        max_length=50,
        choices=PaymentMethod.choices
    )
    
    # --- Price and Status ---
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=50,
        choices=BookingStatus.choices,
        default=BookingStatus.PENDING
    )
    
    # --- Timestamp ---
    booked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Prevents a user from double-booking the same property on the same dates
        unique_together = ('property', 'check_in_date', 'check_out_date')

    def __str__(self):
        return f"Booking for {self.property.title} by {self.user.username}"