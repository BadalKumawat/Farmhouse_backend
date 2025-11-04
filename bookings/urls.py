# bookings/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # --- Guest URLs ---
    # POST /api/bookings/create/
    path('create/', views.BookingCreateView.as_view(), name='booking-create'),

    # GET /api/bookings/my-bookings/
    path('my-bookings/', views.MyBookingListView.as_view(), name='my-booking-list'),

    # GET /api/bookings/my-bookings/1/
    path('my-bookings/<int:id>/', views.MyBookingDetailView.as_view(), name='my-booking-detail'),

    # PATCH /api/bookings/my-bookings/1/cancel/
    path('my-bookings/<int:id>/cancel/', views.MyBookingCancelView.as_view(), name='my-booking-cancel'),

    # --- Vendor URLs ---
    # GET /api/bookings/vendor/
    path('vendor/', views.VendorBookingListView.as_view(), name='vendor-booking-list'),

    # --- Admin URLs ---
    # GET /api/bookings/admin/all/
    path('admin/all/', views.AdminBookingListView.as_view(), name='admin-booking-list'),
]