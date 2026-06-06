from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth import authenticate
from accounts.models import User


class StyledFormMixin:
    field_class = "w-full rounded-lg border border-luxury-line px-4 py-3 text-sm outline-none focus:border-luxury-black"
    auth_field_class = "auth-field"

    def _style_fields(self, use_auth=False):
        css = self.auth_field_class if use_auth else self.field_class
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', css)


class RegisterForm(StyledFormMixin, UserCreationForm):
    email = forms.EmailField(required=True, help_text='Required. A valid email address.')
    phone_number = forms.CharField(max_length=20, required=False, help_text='Optional phone number')

    class Meta:
        model = User
        fields = ('username', 'email', 'phone_number', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._style_fields(use_auth=True)

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('A user with this email already exists.')
        return email


class LoginForm(StyledFormMixin, AuthenticationForm):
    remember_me = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': 'w-4 h-4'}))
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._style_fields(use_auth=True)
        self.error_messages['invalid_login'] = 'Invalid username or password. Please try again.'
    
    def confirm_login_allowed(self, user):
        """Override to add custom lockout checks."""
        # Check if account is locked
        if user.is_locked():
            from django.utils import timezone
            if user.locked_until and user.locked_until > timezone.now():
                remaining_minutes = int((user.locked_until - timezone.now()).total_seconds() / 60)
                raise forms.ValidationError(
                    f'Account is temporarily locked due to multiple failed login attempts. '
                    f'Please try again in {remaining_minutes} minutes.'
                )
        
        # Check if email verification is required
        if user.requires_email_verification and not user.is_email_verified:
            raise forms.ValidationError(
                'Email verification required. Please verify your email before logging in.'
            )
        
        # Check if user is active
        if not user.is_active:
            raise forms.ValidationError(
                'This account is inactive. Please contact support.'
            )
        
        super().confirm_login_allowed(user)


class OTPVerificationForm(forms.Form):
    """Form for OTP verification."""
    
    otp_code = forms.CharField(
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={
            'class': 'w-full rounded-lg border border-luxury-line px-4 py-3 text-sm outline-none focus:border-luxury-black text-center tracking-widest',
            'placeholder': '123456',
            'maxlength': '6',
            'pattern': '[0-9]{6}',
            'inputmode': 'numeric'
        }),
        help_text='Enter the 6-digit code sent to your email'
    )
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.purpose = kwargs.pop('purpose', 'email_verification')
        super().__init__(*args, **kwargs)
    
    def clean_otp_code(self):
        code = self.cleaned_data.get('otp_code')
        
        if not self.user:
            raise forms.ValidationError('User context is required.')
        
        # Verify OTP
        from accounts.utils import verify_otp
        is_valid, result = verify_otp(self.user, code, self.purpose)
        
        if not is_valid:
            raise forms.ValidationError(result)
        
        return code


class ResendOTPForm(forms.Form):
    """Form for requesting OTP resend."""
    
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'w-full rounded-lg border border-luxury-line px-4 py-3 text-sm outline-none focus:border-luxury-black',
            'placeholder': 'Enter your email address'
        })
    )
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        
        try:
            user = User.objects.get(email=email)
            if user.is_email_verified:
                raise forms.ValidationError('This email is already verified.')
            self.cleaned_data['user'] = user
        except User.DoesNotExist:
            raise forms.ValidationError('No account found with this email address.')
        
        return email


class ProfileForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'phone_number')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._style_fields()
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        
        # Check if email is being changed and if it's already taken
        if email != self.instance.email:
            if User.objects.filter(email=email).exists():
                raise forms.ValidationError('A user with this email already exists.')
        
        return email


class PasswordResetRequestForm(forms.Form):
    """Form for requesting password reset."""
    
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'w-full rounded-lg border border-luxury-line px-4 py-3 text-sm outline-none focus:border-luxury-black',
            'placeholder': 'Enter your email address'
        })
    )
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        
        try:
            user = User.objects.get(email=email)
            if not user.is_active:
                raise forms.ValidationError('This account is inactive.')
            self.cleaned_data['user'] = user
        except User.DoesNotExist:
            # Don't reveal if email exists or not for security
            pass
        
        return email
