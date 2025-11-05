from django.urls import path
# 'apis' ko import karein, '*' ko nahi
from .apis import *
from .apis import AdminManagePropertyView as AdminDeletePropertyView

urlpatterns = [
    # GET /properties/ (Public)
    path('', PropertyListView.as_view(), name='property-list'),
    
    # GET /properties/my-properties/ (Sirf Vendor)
    path('my-properties/', VendorPropertyListView.as_view(), name='vendor-property-list'),
    
    # POST /properties/create/ (Sirf Vendor)
    path('create/', PropertyCreateView.as_view(), name='property-create'),

    # URL: /properties/categories/
    path('categories/', CategoryListView.as_view(), name='category-list'),
    
    # URL: /properties/amenities/
    path('amenities/', AmenityListView.as_view(), name='amenity-list'),

    # GET /properties/destinations/
    path('destinations/', DestinationListView.as_view(), name='destination-list'),

    path('certifications/', CertificationListView.as_view(), name='certification-list'),

    path('view-types/', ViewTypeListView.as_view(), name='view-type-list'),

    # URL: /properties/areas/
    path('areas/', AreaListView.as_view(), name='area-list'),
    
    # URL: /properties/property-types/
    path('property-types/', PropertyTypeListView.as_view(), name='property-type-list'),



    # --- Dynamic URLs (Slugs) ab neeche hain ---
    # GET /properties/my-new-property/ (Public)
    path('<slug:slug>/', PropertyDetailView.as_view(), name='property-detail'),
    
    # GET, PUT, PATCH, DELETE /properties/my-new-property/manage/ (Sirf Maalik/Owner)
    path('<slug:slug>/manage/', PropertyManageView.as_view(), name='property-manage'),
    
    # POST /properties/my-new-property/wishlist-toggle/ (Sirf Guest)
    path('<slug:slug>/wishlist-toggle/', ToggleWishlistView.as_view(), name='wishlist-toggle'),

    # --- (ADMIN URLs) ---
    # URL: /properties/admin/all/
    path('admin/all/', AdminPropertyListView.as_view(), name='admin-property-list'),
    
    # URL: /properties/admin/<slug>/approve/
    path('admin/<slug:slug>/approve/', AdminApprovePropertyView.as_view(), name='admin-property-approve'),
    
    # URL: /properties/admin/<slug>/reject/
    path('admin/<slug:slug>/reject/', AdminRejectPropertyView.as_view(), name='admin-property-reject'),
    
    # URL: /properties/admin/<slug>/delete/
    path('admin/<slug:slug>/delete/', AdminDeletePropertyView.as_view(), name='admin-property-delete'),
    # URL: /properties/admin/reports/property-performance/
    path('admin/reports/property-performance/', AdminPropertyPerformanceReportView.as_view(), name='admin-report-property')

]



