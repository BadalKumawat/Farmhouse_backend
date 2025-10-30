from rest_framework import generics, permissions, status
from .models import *
from .serializers import *
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.contrib.auth.tokens import default_token_generator
from rest_framework_simplejwt.views import TokenObtainPairView
from django.core.mail import send_mail
from django.conf import settings
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from rest_framework_simplejwt.tokens import RefreshToken



class UserRegistrationView(generics.CreateAPIView):
    """
    API view to create a new user.
    """
    queryset = CustomUser.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]


class EmailVerificationView(APIView):
    """
    API view to verify email with token.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, uidb64, token):
        try:
            # 1. URL se UID aur User ko decode karein
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = CustomUser.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
            user = None

        # 2. Check karein ki user aur token valid hain
        if user is not None and default_token_generator.check_token(user, token):
            # 3. User ko Active karein
            user.is_active = True
            user.status = CustomUser.Status.ACTIVE # Ya 'Verified'
            user.save()
            
            # Yahan par aap user ko frontend login page par redirect kar sakte hain
            # Abhi ke liye success message bhejte hain
            return Response(
                {'message': 'Email verified successfully! You can now login.'}, 
                status=status.HTTP_200_OK
            )
        else:
            # 4. Agar link galat ya expired hai
            return Response(
                {'error': 'Invalid verification link.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
class MyTokenObtainPairView(TokenObtainPairView):
    """
    Takes a set of user credentials and returns an access and refresh
    JSON web token pair, along with user data.
    """
    serializer_class = MyTokenObtainPairSerializer


class PasswordResetRequestView(generics.GenericAPIView):
    """
    API view to request a password reset.
    """
    serializer_class = PasswordResetRequestSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        
        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            # Email nahi mila to bhi "success" dikhayein, security ke liye
            return Response(
                {'message': 'If an account with this email exists, a password reset link has been sent.'},
                status=status.HTTP_200_OK
            )
            
        # Token aur Link banayein (Email verification jaisa)
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        
        # (Note: 'http://localhost:3000' aapke frontend ka URL hoga)
        reset_url = f"http://localhost:3000/password-reset-confirm/{uid}/{token}/"
        
        subject = 'Reset your password for Farmstay'
        message = f"""
        Hi {user.first_name},

        Someone requested a password reset for your account.
        If this was not you, please ignore this email.
        
        Click the link below to set a new password:
        {reset_url}

        Thanks,
        The Farmstay Team
        """
        
        send_mail(
            subject, message, settings.DEFAULT_FROM_EMAIL, [user.email],
            fail_silently=False,
        )
        
        return Response(
            {'message': 'If an account with this email exists, a password reset link has been sent.'},
            status=status.HTTP_200_OK
        )


class PasswordResetConfirmView(generics.GenericAPIView):
    """
    API view to confirm password reset and set a new password.
    """
    serializer_class = PasswordResetConfirmSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, uidb64, token, *args, **kwargs):
        try:
            # URL se UID aur User ko decode karein
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = CustomUser.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
            user = None

        # Check karein ki user aur token valid hain
        if user is None or not default_token_generator.check_token(user, token):
            return Response(
                {'error': 'Invalid reset link.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Agar link sahi hai, to naya password set karein
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_password = serializer.validated_data['password']
        
        user.set_password(new_password)
        user.save()
        
        return Response(
            {'message': 'Password has been reset successfully. You can now login.'},
            status=status.HTTP_200_OK
        )
    

class LogoutView(APIView):
    """
    API view to blacklist refresh token on logout.
    """
    permission_classes = [permissions.IsAuthenticated] # Sirf login user hi logout kar sakta hai

    def post(self, request):
        try:
            # Frontend ko 'refresh' token body mein bhejna hoga
            refresh_token = request.data["refresh"]
            
            if not refresh_token:
                return Response(
                    {'error': 'Refresh token is required.'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            # Token ko blacklist karein
            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response(
                {'message': 'Logout successful.'}, 
                status=status.HTTP_205_RESET_CONTENT
            )
        except Exception as e:
            # Agar token galat hai ya expire ho chuka hai
            return Response(
                {'error': 'Invalid token or token already blacklisted.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        

class UserDashboardView(generics.RetrieveAPIView):
    # Sirf login kiye hue users hi ise access kar sakte hain
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserProfileSerializer

    def get_object(self):
        # 'request.user' hamesha logged-in user hota hai
        return self.request.user