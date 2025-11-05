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

    # DELETE /users/delete-account/
    path('delete-account/', DeleteAccountView.as_view(), name='delete-account'),


    # --- (ADMIN URLs) ---
    # URL: /users/admin/users/
    path('admin/users/', AdminUserListView.as_view(), name='admin-user-list'),
    
    # URL: /users/admin/users/<id>/delete/
    path('admin/users/<uuid:id>/delete/', AdminManageUserView.as_view(), name='admin-user-delete'),
    
    # URL: /users/admin/vendors/
    path('admin/vendors/', AdminVendorListView.as_view(), name='admin-vendor-list'),
    
    # URL: /users/admin/vendors/<id>/approve/
    path('admin/vendors/<uuid:id>/approve/', AdminApproveVendorView.as_view(), name='admin-vendor-approve'),
    
    # URL: /users/admin/vendors/<id>/delete/
    path('admin/vendors/<uuid:id>/delete/', AdminManageUserView.as_view(), name='admin-vendor-delete'),
    
    # URL: /users/admin/reports/user-growth/
    path('admin/reports/user-growth/', AdminUserGrowthReportView.as_view(), name='admin-report-user-growth'),
    
]