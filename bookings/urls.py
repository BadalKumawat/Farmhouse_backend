# bookings/urls.py
from django.urls import path
from . import views

UUID_REGEX = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
urlpatterns = [
    # --- Guest URLs ---
    # POST /api/bookings/create/
    path('create/', views.BookingCreateView.as_view(), name='booking-create'),

    # GET /api/bookings/my-bookings/
    path('my-bookings/', views.MyBookingListView.as_view(), name='my-booking-list'),

    # GET /api/bookings/my-bookings/1/
    path('my-bookings/<uuid:id>/', views.MyBookingDetailView.as_view(), name='my-booking-detail'),

    # PATCH /api/bookings/my-bookings/1/cancel/
    path('my-bookings/<uuid:id>/cancel/', views.MyBookingCancelView.as_view(), name='my-booking-cancel'),

    # --- Vendor URLs ---
    # GET /api/bookings/vendor/
    path('vendor/', views.VendorBookingListView.as_view(), name='vendor-booking-list'),

    # --- Vendor Manage URL ---
    # PATCH /api/bookings/vendor/1/manage/
    path('vendor/<uuid:id>/manage/', views.VendorManageBookingView.as_view(), name='vendor-booking-manage'),

    # --- Admin URLs ---
    # GET /api/bookings/admin/all/
    path('admin/all/', views.AdminBookingListView.as_view(), name='admin-booking-list'),

    # --- Admin Manage URL ---
    # PATCH /api/bookings/admin/1/manage/
    path('admin/<uuid:id>/manage/', views.AdminManageBookingView.as_view(), name='admin-booking-manage'),

    path('admin/reports/booking-report/', views.AdminBookingReportView.as_view(),name = 'admin-report-booking')
]