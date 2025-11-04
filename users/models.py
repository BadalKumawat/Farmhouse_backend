from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser, PermissionsMixin
from django.conf import settings # AUTH_USER_MODEL ke liye
from properties.models import Property # Wishlist ke liye
import uuid

class CustomUserManager(BaseUserManager):
    
    def create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError('Email address is required')
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password) # Password hash karein
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role', 'admin') # Superuser ka role 'admin'
        extra_fields.setdefault('status', 'active') # Superuser ka status 'active'

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(email, password, **extra_fields)

# ---  Custom User Model ---
class CustomUser(AbstractBaseUser, PermissionsMixin):
    
    # --- Role Choices 
    class Role(models.TextChoices):
        GUEST = 'guest', 'Guest'
        VENDOR = 'vendor', 'Vendor'
        ADMIN = 'admin', 'Admin'

    # --- Status Choices ---
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        ACTIVE = 'active', 'Active'
        VERIFIED = 'verified', 'Verified'

    
    # 1. Email ( yeh Login Field )
    email = models.EmailField(unique=True) 
    
    # 2. Full Name (hum ise first/last name mein store karenge)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    
    # 3. Mobile Number
    phone_number = models.CharField(max_length=20, unique=True)
    
    # 4. Role aur Status 
    role = models.CharField(
        max_length=50,
        choices=Role.choices,
        default=Role.GUEST
    )
    status = models.CharField(
        max_length=50,
        choices=Status.choices,
        default=Status.PENDING
    )
    
    # 5. Wishlist 
    wishlist = models.ManyToManyField(
        Property, 
        blank=True, # Wishlist khaali ho sakti hai
        related_name="wishlisted_by"
    )

    #profile picture field
    profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True)

    # (Yeh fields sirf Vendor role ke liye relevant hain)
    notify_new_bookings = models.BooleanField(default=True)
    notify_guest_messages = models.BooleanField(default=True)
    notify_cancellations = models.BooleanField(default=False)

    notify_booking_confirmations = models.BooleanField(default=True)
    notify_promotional_offers = models.BooleanField(default=False)
    notify_account_activity = models.BooleanField(default=True)

    # --- Django ke zaroori fields ---
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False) # Verification ke liye default FALSE
    is_superuser = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    
    # --- Configuration ---
    
    # 1. Login ke liye 'email' ka istemal karein
    USERNAME_FIELD = 'email' 
    
    # 2. createsuperuser ke time 'username' na poochein
    REQUIRED_FIELDS = ['first_name', 'last_name', 'phone_number'] 

    # Manager ko link karein
    objects = CustomUserManager()
    
    @property
    def full_name(self):
        "Returns the user's full name."
        return f"{self.first_name} {self.last_name}"

    def __str__(self):
        return self.email