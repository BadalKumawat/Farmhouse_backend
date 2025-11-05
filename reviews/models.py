from django.db import models
from django.conf import settings # For CustomUser
from properties.models import Property # To link to the Property model
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid

class Review(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # Link to the user who is giving the review (must be a 'guest')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reviews',
        limit_choices_to={'role': 'guest'}
    )
    
    # Link to the property being reviewed
    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    
    # Rating (1 to 5)
    rating = models.PositiveIntegerField(
        validators=[
            MinValueValidator(1), 
            MaxValueValidator(5)
        ],
        help_text="Rating must be between 1 and 5"
    )
    
    # The review comment
    comment = models.TextField()
    
    # Timestamp
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Prevents a user from reviewing the same property more than once
        unique_together = ('user', 'property')

    def __str__(self):
        return f"Review for {self.property.title} by {self.user.full_name} ({self.rating} stars)"
    


class ContactMessage(models.Model):
    """
    Model to store messages from the /contact form.
    """
    class SubjectChoices(models.TextChoices):
        GUEST = 'guest_inquiry', 'Guest Inquiry'
        HOST = 'host_application', 'Host/Vendor Application'
        SUPPORT = 'support_issue', 'Technical Support'
        PARTNER = 'partner_inquiry', 'Partnership Inquiry'
        OTHER = 'other', 'Other'

    full_name = models.CharField(max_length=150)
    email = models.EmailField(max_length=100)
    phone_number = models.CharField(max_length=20, blank=True, null=True) # Optional
    subject = models.CharField(max_length=50, choices=SubjectChoices.choices, default=SubjectChoices.OTHER)
    message = models.TextField()
    
    # Tracking
    is_read = models.BooleanField(default=False) # Admin ke liye
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.full_name} ({self.subject})"