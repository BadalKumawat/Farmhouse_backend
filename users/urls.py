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
    path('dashboard/wishlist/', WishlistListView.as_view(), name='dashboard-wishlist'),

    path('change-password/', ChangePasswordView.as_view(), name='change-password'),

    # DELETE /api/auth/delete-account/
    path('delete-account/', DeleteAccountView.as_view(), name='delete-account'),


    # --- (ADMIN URLs) ---
    # URL: /api/auth/admin/users/
    path('admin/users/', AdminUserListView.as_view(), name='admin-user-list'),
    
    # URL: /api/auth/admin/users/<id>/delete/
    path('admin/users/<int:id>/delete/', AdminManageUserView.as_view(), name='admin-user-delete'),
    
    # URL: /api/auth/admin/vendors/
    path('admin/vendors/', AdminVendorListView.as_view(), name='admin-vendor-list'),
    
    # URL: /api/auth/admin/vendors/<id>/approve/
    path('admin/vendors/<int:id>/approve/', AdminApproveVendorView.as_view(), name='admin-vendor-approve'),
    
    # URL: /api/auth/admin/vendors/<id>/delete/
    path('admin/vendors/<int:id>/delete/', AdminManageUserView.as_view(), name='admin-vendor-delete'), # Wahi user delete view


    
]