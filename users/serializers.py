from rest_framework import serializers
from .models import CustomUser

# --- Imports for Email Verification ---
from django.core.mail import send_mail
from django.conf import settings
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
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

            # --- 2. Check karein ki Admin ko notification chahiye ya nahi ---
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
        }
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


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for displaying AND updating user profile details.
    """
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
            'status'             # Read-only
        ]
        # Yahaan sirf woh fields daalein jo user badal nahi sakta
        read_only_fields = ['id', 'email', 'role', 'status']

    def update(self, instance, validated_data):
        # Yeh check karta hai ki user galti se email ya role ko na badal de
        if 'email' in validated_data:
            raise serializers.ValidationError({"email": "Email cannot be changed."})
        if 'role' in validated_data:
            raise serializers.ValidationError({"role": "Role cannot be changed."})

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
