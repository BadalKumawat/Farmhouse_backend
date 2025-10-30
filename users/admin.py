from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser
from .forms import CustomUserCreationForm, CustomUserChangeForm # Naye Forms ko import karein

class CustomUserAdmin(UserAdmin):
    
    # --- Form Settings ---
    # Yeh forms.py se hamare naye forms ko istemal karega
    form = CustomUserChangeForm       # Edit karne ke liye
    add_form = CustomUserCreationForm   # Naya user banane ke liye
    # --------------------

    # Admin list mein yeh dikhayein
    list_display = ('email', 'first_name', 'last_name', 'role', 'status', 'is_staff')
    list_filter = ('role', 'status', 'is_staff', 'is_active')
    
    # --- Edit Page Form ---
    # 'fieldsets' batata hai ki 'Edit' page kaisa dikhega
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'phone_number')}),
        ('Permissions', {'fields': ('role', 'status', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
        ('Wishlist', {'fields': ('wishlist',)}),
    )
    
    # --- (FIX) Add Page Form ---
    # 'add_fieldsets' batata hai ki 'Add' page kaisa dikhega
    # Ab yeh hamare 'add_form' (CustomUserCreationForm) se fields lega
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'phone_number', 'role', 'status', 'password', 'password2'),
        }),
    )
    
    # --- (FIX) ReadOnly Fields ---
    readonly_fields = ('last_login', 'date_joined')
    
    # --- Other Settings ---
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)
    filter_horizontal = ('groups', 'user_permissions', 'wishlist')

admin.site.register(CustomUser, CustomUserAdmin)