from django.urls import path
from . import views

urlpatterns = [
    # --- Vendor API ---
    # GET /reviews/vendor/
    path('vendor/', views.VendorReviewListView.as_view(), name='vendor-review-list'),

    # --- Admin APIs ---
    # GET /reviews/admin/all/
    path('admin/all/', views.AdminReviewListView.as_view(), name='admin-review-list'),
    # DELETE /reviews/admin/1/delete/
    path('admin/<uuid:id>/delete/', views.AdminManageReviewView.as_view(), name='admin-review-delete'),

    path('video-testimonials/', views.VideoTestimonialListView.as_view(), name='video-testimonials-list'),
    
    path('property/<slug:slug>/upload-video/', views.VideoTestimonialCreateView.as_view(), name='video-testimonial-create'),

    # --- Property Specific APIs ---
    # GET /reviews/property/<slug>/
    path('property/<slug:slug>/', views.PropertyReviewListView.as_view(), name='review-list-property'),
    # POST /reviews/property/<slug>/create/
    path('property/<slug:slug>/create/', views.ReviewCreateView.as_view(), name='review-create'),

    path('contact/', views.ContactMessageCreateView.as_view(), name='contact-message-create'),
]