from django.db import models
from django.conf import settings # For CustomUser
from properties.models import Property # To link to the Property model
from django.core.validators import MinValueValidator, MaxValueValidator

class Review(models.Model):
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
        return f"Review for {self.property.title} by {self.user.username} ({self.rating} stars)"