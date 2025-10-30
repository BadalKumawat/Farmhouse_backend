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

        # User create karein (CustomUserManager ka 'create_user' call hoga)
        # Email, first_name, last_name, phone_number pass honge
        user = CustomUser.objects.create_user(password=password, **validated_data)
        
        # (Email verification wala logic yahaan se move ho gaya hai,
        #  kyunki 'create_user' ab use handle kar raha hai)
        # Hum email verification ko alag se trigger karenge
        
        # --- Email Bhejne ka Logic (Wahi purana) ---
        try:
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            verification_url = f"http://127.0.0.1:8000/api/auth/verify-email/{uid}/{token}/"
            
            subject = 'Verify your email for Farmstay'
            message = f"Hi {user.first_name},\n\nPlease click the link to verify your email:\n{verification_url}"
            
            send_mail(
                subject, message, settings.DEFAULT_FROM_EMAIL, [user.email],
                fail_silently=False,
            )
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
    Serializer for displaying user profile details.
    """
    class Meta:
        model = CustomUser
        # Yeh fields hum API response mein dikhayenge
        fields = [
            'id',  
            'email', 
            'first_name', 
            'last_name', 
            'phone_number',
            'role', 
            'status'
        ]
        # Hum nahi chahte ki koi is API se data 'write' (POST/PUT) kare
        read_only_fields = fields


