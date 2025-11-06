from django import forms
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from .models import CustomUser

class CustomUserCreationForm(forms.ModelForm):
    """
    A form for creating new users.
    """
    # Password fields ko manually define karein
    password = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Password confirmation', widget=forms.PasswordInput)

    class Meta:
        model = CustomUser
        # 'Add user' form mein yeh fields dikhengi
        fields = ('email', 'first_name', 'last_name', 'phone_number', 'role', 'status')

    def clean_password2(self):
        # Check karein ki dono password match karte hain
        password = self.cleaned_data.get("password")
        password2 = self.cleaned_data.get("password2")
        if password and password2 and password != password2:
            raise forms.ValidationError("Passwords do not match.")
        return password2

    def save(self, commit=True):
        # Save the provided password in hashed format
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


class CustomUserChangeForm(forms.ModelForm):
    """
    A form for updating users in the admin.
    """
    password = ReadOnlyPasswordHashField(
        label='Password',
        help_text=(
            "Raw passwords are not stored. You can change the password "
            "using <a href=\"../password/\">this form</a>."
        )
    )

    class Meta:
        model = CustomUser
        # 'Edit user' form mein yeh fields dikhengi
        fields = ('email', 'first_name', 'last_name','state','city', 'phone_number', 'role', 'status', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')

    # --- YEH FIX HAI ---
    # Humne poora '__init__' method yahaan se HATA diya hai,
    # kyunki 'admin.py' field order ko pehle hi handle kar raha hai.
    # -------------------