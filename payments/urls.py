# payments/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # --- Guest URL ---
    # GET /payments/my-history/
    path('my-history/', views.MyPaymentListView.as_view(), name='my-payment-history'),

    # --- Vendor URL ---
    # GET /payments/vendor-revenue/
    path('vendor-revenue/', views.VendorRevenueView.as_view(), name='vendor-revenue'),

    # --- Admin URLs ---
    # GET /payments/admin/all/
    path('admin/all/', views.AdminPaymentListView.as_view(), name='admin-payment-list'),

    # GET /payments/admin/reports/revenue-report/
    path('admin/reports/revenue-report/', views.AdminRevenueReportView.as_view(), name='admin-report-revenue')

]