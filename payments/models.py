from django.db import models
from bookings.models import Booking
import uuid

class Payment(models.Model):
    class PaymentStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        COMPLETED = 'completed', 'Completed'
        FAILED = 'failed', 'Failed'
        REFUNDED = 'refunded', 'Refunded'

    # Payment ko Booking se link karein
    booking = models.OneToOneField(
        Booking, 
        on_delete=models.CASCADE, 
        related_name='payment'
    )

    '''
        razorpay_order_id = models.CharField(max_length=100, null=True, blank=True)
        razorpay_payment_id = models.CharField(max_length=100, null=True, blank=True)
        razorpay_signature = models.CharField(max_length=255, null=True, blank=True)
    '''

    # Transaction ID (e.g., "txn_1" or Stripe ID)
    transaction_id = models.CharField(max_length=100, unique=True, default=uuid.uuid4)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=50, 
        choices=PaymentStatus.choices, 
        default=PaymentStatus.PENDING
    )
    payment_method = models.CharField(max_length=50) # 'Online' or 'Cash'

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Payment {self.transaction_id} for Booking {self.booking.id}"