from django.urls import path
from .apis import *
urlpatterns = [
    # SignUp // Registration  URL
    path('register/', UserRegistrationView.as_view(), name='register'),

    #Email Verify URL
    path(
        'verify-email/<str:uidb64>/<str:token>/', 
        EmailVerificationView.as_view(), 
        name='verify-email'
    ),

    #Password Reset URL
    path(
        'password-reset-request/', 
        PasswordResetRequestView.as_view(), 
        name='password-reset-request'
    ),

    #Password Reset Confirmation URL
    path(
        'password-reset-confirm/<str:uidb64>/<str:token>/', 
        PasswordResetConfirmView.as_view(), 
        name='password-reset-confirm'
    ),

    #logout URL
    path('logout/', LogoutView.as_view(), name='logout'), 

    path('dashboard/', UserDashboardView.as_view(), name='dashboard'),
]