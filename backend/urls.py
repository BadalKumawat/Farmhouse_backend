"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

# backend/urls.py

from django.contrib import admin
from django.urls import path, include

# 1. simplejwt के डिफ़ॉल्ट व्यू की जगह,
#    सिर्फ 'TokenRefreshView' को इम्पोर्ट करें
from rest_framework_simplejwt.views import TokenRefreshView

# 2. अपने 'users/apis.py' से 'MyTokenObtainPairView' को इम्पोर्ट करें
from users.apis import MyTokenObtainPairView 

from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # --- JWT Login URL (UPDATED) ---
    # 3. यहाँ डिफ़ॉल्ट व्यू की जगह 'MyTokenObtainPairView' का इस्तेमाल करें
    path(
        'api/token/', 
        MyTokenObtainPairView.as_view(),  # <-- यह बदल गया है
        name='token_obtain_pair'
    ),
    
    # --- JWT Refresh URL (यह वैसा ही है) ---
    path(
        'api/token/refresh/', 
        TokenRefreshView.as_view(), 
        name='token_refresh'
    ),
    
    # --- Users App URLs (यह वैसा ही है) ---
    path('api/auth/', include('users.urls')),

    # Yeh 'properties/urls.py' file ko hamare project se jodta hai
    path('api/properties/', include('properties.urls')),

    # --- SWAGGER URLs ---
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    # Swagger UI:
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    # Redoc UI:
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]