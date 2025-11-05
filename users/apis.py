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
from .permissions import IsAdminRole
from rest_framework import status
from properties.models import Property
from properties.serializers import PropertyListSerializer
from django.utils import timezone
from datetime import datetime
from dateutil.relativedelta import relativedelta
from django.db.models import Count
from django.db.models.functions import TruncMonth


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
        

class UserDashboardView(generics.RetrieveUpdateAPIView): # <-- RetrieveUpdateAPIView ka istemal karein
    """
    API view for logged-in user's dashboard (GET) and Profile Update (PUT/PATCH).
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserProfileSerializer

    def get_object(self):
        # 'request.user' hamesha logged-in user hota hai
        return self.request.user
    

class AdminUserListView(generics.ListAPIView):
    """
    Admin ke liye: Saare 'guest' users ki list.
    (image_545375.png)
    """
    queryset = CustomUser.objects.filter(role='guest').order_by('-date_joined')
    serializer_class = AdminUserListSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminRole]

class AdminVendorListView(generics.ListAPIView):
    """
    Admin ke liye: Saare 'vendor' users ki list.
    (image_54537d.png)
    """
    queryset = CustomUser.objects.filter(role='vendor').order_by('-date_joined')
    serializer_class = AdminUserListSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminRole]

class AdminManageUserView(generics.DestroyAPIView):
    """
    Admin ke liye: Ek user/vendor ko delete karna.
    (Dono ke 'Delete' button ke liye)
    """
    queryset = CustomUser.objects.all()
    permission_classes = [permissions.IsAuthenticated, IsAdminRole]
    lookup_field = 'slug' # Hum ID se delete karenge

class AdminApproveVendorView(APIView):
    """
    Admin ke liye: Ek 'pending' vendor ko 'verified' karna.
    (image_54537d.png ka 'Approve' button)
    """
    permission_classes = [permissions.IsAuthenticated, IsAdminRole]

    def patch(self, request, slug, *args, **kwargs):
        try:
            vendor = CustomUser.objects.get(slug=slug, role='vendor')
        except CustomUser.DoesNotExist:
            return Response({'error': 'Vendor not found.'}, status=status.HTTP_404_NOT_FOUND)
        
        # Vendor ko 'verified' (ya 'active') karein
        vendor.status = 'verified' # Ya 'active' jo bhi aapka logic hai
        vendor.save()
        return Response({'message': 'Vendor approved successfully.'}, status=status.HTTP_200_OK)
    
class AdminUserGrowthReportView(APIView):
    """
    Admin ke liye: 'User Growth Report' generate karna (date range ke sath).
    """
    permission_classes = [permissions.IsAuthenticated, IsAdminRole]

    def get(self, request, *args, **kwargs):
        try:
            end_date = datetime.strptime(request.query_params.get('end_date'), '%Y-%m-%d').date()
        except (ValueError, TypeError):
            end_date = timezone.now().date()
        try:
            start_date = datetime.strptime(request.query_params.get('start_date'), '%Y-%m-%d').date()
        except (ValueError, TypeError):
            start_date = end_date - relativedelta(days=30)

        # Base Queryset
        users_in_range = CustomUser.objects.filter(
            date_joined__range=[start_date, end_date]
        )
        
        # Data Calculate karein
        new_users_count = users_in_range.count()
        
        # Chart Data: Users Over Time
        chart_data = users_in_range.annotate(
            month=TruncMonth('date_joined')
        ).values('month').annotate(
            count=Count('id')
        ).order_by('month')

        users_over_time = [
            {'month': item['month'].strftime('%Y-%m'), 'count': item['count']}
            for item in chart_data
        ]
        
        data = {
            'new_user_in_range': new_users_count,
            'user_over_time': users_over_time
        }
        serializer = UserGrowthReportSerializer(instance=data)
        #serializer.is_valid(raise_exception=True)
        return Response(serializer.data)
    

class ChangePasswordView(generics.UpdateAPIView):
    """
    API view for a logged-in user to change their password.
    """
    serializer_class = ChangePasswordSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response({'message': 'Password updated successfully.'}, status=status.HTTP_200_OK)
    

class WishlistListView(generics.ListAPIView):
    """
    API to list all properties in the logged-in user's wishlist.
    (Used for /dashboard/wishlist route)
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PropertyListSerializer
    
    def get_queryset(self):
        # Logged-in user ki 'wishlist' field se properties nikalna
        user = self.request.user
        return user.wishlist.all().order_by('-created_at')

    def get_serializer_context(self):
        # Wishlist serializer ko 'request' object pass karna zaroori hai
        context = super().get_serializer_context()
        context.update({'request': self.request})
        return context


class DeleteAccountView(APIView):
    """
    API to allow the logged-in user (Guest/Vendor/Admin) to delete their own account.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request): # DELETE ki jagah POST ka istemal karein taaki body mein data le saken
        user = request.user
        
        # 1. Serializer ko run karein aur context mein user ko bhejein
        serializer = AccountDeleteSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        # 2. Agar password sahi hai (jo serializer ne check kiya), toh deletion process shuru karein
        
        # 3. Tokens ko blacklist karein (Safety)
        from rest_framework_simplejwt.tokens import RefreshToken
        try:
            token = RefreshToken.for_user(user)
            token.blacklist()
        except Exception:
            pass # Ignore if no tokens are found
            
        # 4. User aur uske saare data ko delete karein (CASCADE delete)
        user.delete()
        
        return Response({'message': 'Account deleted successfully.'}, status=status.HTTP_204_NO_CONTENT)