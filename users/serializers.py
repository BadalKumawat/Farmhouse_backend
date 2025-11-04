from rest_framework import serializers
from .models import CustomUser

# --- Imports for Email Verification ---
from django.core.mail import send_mail
from django.conf import settings
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from site_settings.models import SiteSettings
from decouple import config

# -------------------------------------


class UserRegistrationSerializer(serializers.ModelSerializer):
    # 'confirm password' field (yeh model mein nahi hai)
    password2 = serializers.CharField(
        style={'input_type': 'password'}, 
        write_only=True
    )

    class Meta:
        model = CustomUser
        fields = [
            'email',         
            'first_name',    
            'last_name',
           'phone_number',  
            'password', 
            'password2'
        ]
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError("Passwords do not match.")
        
        # Email aur Phone Number unique hain ya nahi, yeh DRF model se 
        # apne aap check kar lega (kyunki model mein unique=True hai)
        
        return data

    def create(self, validated_data):
        # 'password2' ko data se hata dein
        validated_data.pop('password2')

        # 'password' ko alag se nikal lein
        password = validated_data.pop('password')

        # User create karein
        user = CustomUser.objects.create_user(password=password, **validated_data)

        # --- Email Bhejne ka Logic (UPDATED) ---
        try:
            # --- 1. User ko verification email bhejein (Pehle jaisa) ---
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            verification_url = f"http://127.0.0.1:8000/api/auth/verify-email/{uid}/{token}/"
            subject = 'Verify your email for Farmstay'
            message = f"Hi {user.first_name},\n\nPlease click the link to verify your email:\n{verification_url}"
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])

            # --- For Admin Notificatio of updation ---
            settings_obj = SiteSettings.objects.first()
            if settings_obj and settings_obj.notify_new_user:

                admin_subject = 'New User Registration on Farmstay'
                admin_message = f"A new user has registered:\n\nEmail: {user.email}\nName: {user.full_name}\nRole: {user.role}"

                # Admin ka email .env file se lein
                admin_email = config('ADMIN_EMAIL', default=None)
                if admin_email:
                    send_mail(admin_subject, admin_message, settings.DEFAULT_FROM_EMAIL, [admin_email])

        except Exception as e:
            print(f"Error sending email: {e}")

        return user


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Token (payload) mein 'email' aur 'role' daalein (username ki jagah)
        token['email'] = user.email
        token['role'] = user.role
        return token

    def validate(self, attrs):
        # Default 'validate' method ko call karein (jo tokens generate karega)
        data = super().validate(attrs)
        profile_pic_url = None
        if self.user.profile_picture:
            profile_pic_url = self.user.profile_picture.url

        # 'data' (jo response hai) usmein user details add karein
        # (username hatakar phone_number add kiya hai)
        data['user'] = {
            'id': self.user.id,
            'email': self.user.email,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'phone_number': self.user.phone_number, # Naya field
            'role': self.user.role,
            'status': self.user.status,
            'profile_picture': profile_pic_url,
        }
        if not self.user.is_active:
             raise serializers.ValidationError('Account is inactive. Please verify your email.')

        return data
    
class PasswordResetRequestSerializer(serializers.Serializer):
    """
    Serializer for requesting a password reset e-mail.
    """
    email = serializers.EmailField(required=True)

class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    Serializer for confirming a password reset.
    """
    password = serializers.CharField(write_only=True, required=True, min_length=8)
    password2 = serializers.CharField(write_only=True, required=True)

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError("Passwords do not match.")
        return data
    
class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True, required=True)
    new_password = serializers.CharField(write_only=True, required=True, min_length=8)
    new_password2 = serializers.CharField(write_only=True, required=True)

    def validate_current_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is not correct.")
        return value

    def validate(self, data):
        if data['new_password'] != data['new_password2']:
            raise serializers.ValidationError("New passwords do not match.")
        return data

    def save(self, **kwargs):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for displaying AND updating user profile details.
    """

    def __init__(self, *args, **kwargs):
        # Pehle default __init__ ko run karein
        super(UserProfileSerializer, self).__init__(*args, **kwargs)

        # Check karein ki 'request' context mein hai ya nahi
        if 'request' in self.context:
            user = self.context['request'].user

            if user and user.is_authenticated:
                # Yeh fields define karein
                vendor_fields = ['notify_new_bookings', 'notify_guest_messages', 'notify_cancellations']
                guest_fields = ['notify_booking_confirmations', 'notify_promotional_offers', 'notify_account_activity']

                if user.role == 'guest':
                    # Agar user GUEST hai, toh VENDOR ki fields hata dein
                    for field_name in vendor_fields:
                        self.fields.pop(field_name, None)
                        
                elif user.role == 'vendor':
                    # Agar user VENDOR hai, toh GUEST ki fields hata dein
                    for field_name in guest_fields:
                        self.fields.pop(field_name, None)


    class Meta:
        model = CustomUser
        # 'email' aur 'role' ko read_only rakhenge
        fields = [
            'id', 
            'email',             # Read-only
            'first_name', 
            'last_name', 
            'phone_number',      
            'role',              # Read-only
            'status',             # Read-only
            'profile_picture',
            # Vendor notification fields
            'notify_new_bookings', 
            'notify_guest_messages', 
            'notify_cancellations',
            # USER notification fields
            'notify_booking_confirmations',
            'notify_promotional_offers',
            'notify_account_activity'
        ]


    extra_kwargs = {
            'email': {'read_only': True},
            'role': {'read_only': True},
            'status': {'read_only': True},
            'id': {'read_only': True},
        }

    def update(self, instance, validated_data):
        # Yeh check karta hai ki user galti se email ya role ko na badal de
        if 'email' in validated_data:
            raise serializers.ValidationError({"email": "Email cannot be changed."})
        if 'role' in validated_data:
            raise serializers.ValidationError({"role": "Role cannot be changed."})
        if 'profile_picture' in self.context['request'].FILES:
            instance.profile_picture = self.context['request'].FILES['profile_picture']

        return super().update(instance, validated_data)


class AdminUserListSerializer(serializers.ModelSerializer):
    """
    Admin dashboard mein Users aur Vendors ki list dikhane ke liye.
    """
    # Hum 'full_name' (property) ka istemal kar rahe hain
    full_name = serializers.CharField(read_only=True)
    
    class Meta:
        model = CustomUser
        # image_545375.png ke hisab se fields
        fields = ['id', 'full_name', 'email', 'phone_number', 'role', 'status', 'date_joined']


class AccountDeleteSerializer(serializers.Serializer):
    """
    Serializer to confirm the user's current password before deletion.
    """
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

    def validate_password(self, value):
        # Context se logged-in user object ko access karein
        user = self.context['request'].user
        
        # Check karein ki diya gaya password user ke DB password se match karta hai
        if not user.check_password(value):
            raise serializers.ValidationError("Incorrect password. Account deletion failed.")
        
        return value
