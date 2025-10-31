from django.db import models
from django.conf import settings # We'll use this to get your CustomUser model
from django.utils.text import slugify
import uuid


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name
    
# Model 1: AMENITY
# These are the checkbox items like 'Wi-Fi', 'Pool', etc.
class Amenity(models.Model):
    name = models.CharField(max_length=100, unique=True)
    # You could add an 'icon' field here later if you want

    class Meta:
        verbose_name_plural = "Amenities" # Fixes 'Amenitys' in admin

    def __str__(self):
        return self.name

# Model 2: PROPERTY
# This is the main model for the farmhouse, villa, etc.
class Property(models.Model):

    # --- Property Type Choices ---
    class PropertyType(models.TextChoices):
        FARMHOUSE = 'farmhouse', 'Farmhouse'
        VILLA = 'villa', 'Villa'
        RESORT = 'resort', 'Resort'
        COTTAGE = 'cottage', 'Cottage'
    
    # --- Basic Details ---
    # We link to the 'Vendor' user
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='properties',
        limit_choices_to={'role': 'vendor'} # Ensures only vendors can be owners
    )


    title = models.CharField(max_length=255, verbose_name="Property Name")


    # random generate krega jo ki property ki id ki jagah use hoga 
    slug = models.SlugField(
        max_length=255, 
        unique=True, 
        default=uuid.uuid4, 
        editable=False
    )

    property_type = models.CharField(max_length=50, choices=PropertyType.choices)

    category = models.ForeignKey(
        Category, 
        on_delete=models.SET_NULL, # Agar category delete ho, to property delete na ho
        null=True,
        blank=True,
        related_name='properties'
    )

    class PropertyStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'

    status = models.CharField(
        max_length=50,
        choices=PropertyStatus.choices,
    )
    
    # --- Location ---
    state = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    area = models.CharField(max_length=255)
    pin_code = models.CharField(max_length=6)
    google_maps_location = models.URLField(max_length=500, blank=True, null=True)

    # --- Description ---
    short_description = models.CharField(max_length=250)
    full_description = models.TextField()

    # --- Pricing ---
    base_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        verbose_name="Base Price per night"
    )
    weekend_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        blank=True, 
        null=True,
        help_text="Leave blank if same as base price"
    )
    extra_guest_charge = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        blank=True, 
        null=True
    )

    # --- Availability ---
    check_in_time = models.TimeField()
    check_out_time = models.TimeField()

    # --- Property Features ---
    bedrooms = models.PositiveIntegerField(default=1)
    bathrooms = models.PositiveIntegerField(default=1)
    max_guests = models.PositiveIntegerField(default=1, verbose_name="Maximum Capacity")
    
    # --- Amenities (from Model 1) ---
    # This is the Many-to-Many link to the Amenity model
    # This will create the checkbox list you wanted
    amenities = models.ManyToManyField(Amenity, blank=True)

    # --- Timestamps ---
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
    

# Model 3: PROPERTY IMAGE
# Allows for multiple images per property
class PropertyImage(models.Model):
    # Link to the Property model
    property = models.ForeignKey(
        Property, 
        on_delete=models.CASCADE, 
        related_name='images'
    )
    # The image file
    image = models.ImageField(upload_to='property_images/')

    def __str__(self):
        return f"Image for {self.property.title}"

# Model 4: BLACKOUT DATE
# Dates when the property is not available
class BlackoutDate(models.Model):
    # Link to the Property model
    property = models.ForeignKey(
        Property, 
        on_delete=models.CASCADE, 
        related_name='blackout_dates'
    )
    date = models.DateField()

    class Meta:
        # Ensures a property can't have the same date blacked out twice
        unique_together = ('property', 'date')

    def __str__(self):
        return f"Blackout on {self.date} for {self.property.title}"