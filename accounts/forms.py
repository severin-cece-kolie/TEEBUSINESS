from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm, SetPasswordForm
from accounts.models import User


# ─────────────────────────────────────────────────────────────
# Shared styling
# ─────────────────────────────────────────────────────────────

INPUT_CLASS = (
    "w-full rounded-xl border border-luxury-line bg-white px-4 py-3.5 text-sm "
    "text-luxury-black placeholder:text-luxury-mid outline-none transition "
    "focus:border-luxury-black focus:ring-2 focus:ring-luxury-black/10"
)


def _strip_help_and_labels(form):
    """Remove every Django default help_text so nothing leaks into the UI."""
    for field in form.fields.values():
        field.help_text = ''


class LoginForm(AuthenticationForm):
    """Email + password sign-in. The field is still named `username`
    (AuthenticationForm contract) but is labelled and validated as email."""

    remember_me = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'h-4 w-4 rounded border-luxury-line text-luxury-black focus:ring-luxury-black/20'
        }),
    )

    error_messages = {
        'invalid_login': 'The email or password entered is incorrect.',
        'inactive': 'Please verify your email address to activate your account.',
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'Email'
        self.fields['username'].widget = forms.EmailInput(attrs={
            'class': INPUT_CLASS,
            'placeholder': 'you@example.com',
            'autocomplete': 'email',
            'autofocus': True,
        })
        self.fields['password'].widget = forms.PasswordInput(attrs={
            'class': INPUT_CLASS,
            'placeholder': 'Password',
            'autocomplete': 'current-password',
        })
        _strip_help_and_labels(self)

    def confirm_login_allowed(self, user):
        from django.utils import timezone

        if user.is_locked():
            remaining = 15
            if user.locked_until and user.locked_until > timezone.now():
                remaining = max(1, int((user.locked_until - timezone.now()).total_seconds() / 60))
            raise forms.ValidationError(
                f'Too many attempts. Please try again in {remaining} minutes.',
                code='locked',
            )

        if user.requires_email_verification and not user.is_email_verified:
            raise forms.ValidationError(
                'Please verify your email address to continue.',
                code='needs_verification',
            )

        if not user.is_active:
            raise forms.ValidationError(
                self.error_messages['inactive'],
                code='inactive',
            )


class RegisterForm(UserCreationForm):
    """Premium registration: First name, Last name, Email, Password, Confirm."""

    first_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': INPUT_CLASS, 'placeholder': 'First name', 'autocomplete': 'given-name',
        }),
        error_messages={'required': 'Please enter your first name.'},
    )
    last_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': INPUT_CLASS, 'placeholder': 'Last name', 'autocomplete': 'family-name',
        }),
        error_messages={'required': 'Please enter your last name.'},
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': INPUT_CLASS, 'placeholder': 'you@example.com', 'autocomplete': 'email',
        }),
        error_messages={
            'required': 'Please enter your email address.',
            'invalid': 'Please enter a valid email address.',
        },
    )

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget = forms.PasswordInput(attrs={
            'class': INPUT_CLASS, 'placeholder': 'Password', 'autocomplete': 'new-password',
        })
        self.fields['password2'].widget = forms.PasswordInput(attrs={
            'class': INPUT_CLASS, 'placeholder': 'Confirm password', 'autocomplete': 'new-password',
        })
        self.error_messages['password_mismatch'] = 'The two passwords don’t match.'
        _strip_help_and_labels(self)

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        email = self.cleaned_data['email']
        user.email = email
        user.username = email  # email doubles as the unique username
        if commit:
            user.save()
        return user


class OTPVerificationForm(forms.Form):
    """6-digit OTP verification."""

    otp_code = forms.CharField(
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={
            'class': (
                'w-full rounded-xl border border-luxury-line bg-white px-4 py-4 text-center '
                'text-2xl font-semibold tracking-[0.5em] outline-none transition '
                'focus:border-luxury-black focus:ring-2 focus:ring-luxury-black/10'
            ),
            'placeholder': '••••••',
            'maxlength': '6',
            'inputmode': 'numeric',
            'pattern': '[0-9]*',
            'autocomplete': 'one-time-code',
            'autofocus': True,
        }),
        error_messages={
            'required': 'Please enter your verification code.',
            'min_length': 'Your code must be 6 digits.',
            'max_length': 'Your code must be 6 digits.',
        },
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.purpose = kwargs.pop('purpose', 'email_verification')
        super().__init__(*args, **kwargs)
        _strip_help_and_labels(self)

    def clean_otp_code(self):
        code = self.cleaned_data.get('otp_code')
        if not self.user:
            raise forms.ValidationError('Something went wrong. Please request a new code.')

        from accounts.utils import verify_otp
        is_valid, result = verify_otp(self.user, code, self.purpose)
        if not is_valid:
            raise forms.ValidationError(result)
        return code


class ResendOTPForm(forms.Form):
    """Request a fresh verification code."""

    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': INPUT_CLASS, 'placeholder': 'you@example.com', 'autocomplete': 'email',
        }),
        error_messages={
            'required': 'Please enter your email address.',
            'invalid': 'Please enter a valid email address.',
        },
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _strip_help_and_labels(self)

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            raise forms.ValidationError('We couldn’t find an account with this email.')
        if user.is_email_verified:
            raise forms.ValidationError('This email is already verified. You can sign in.')
        self.cleaned_data['user'] = user
        return email


class ProfileForm(forms.ModelForm):
    """Account details editing."""

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'phone_number', 'address', 'city', 'country')
        widgets = {
            'first_name': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'First name'}),
            'last_name': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Last name'}),
            'email': forms.EmailInput(attrs={'class': INPUT_CLASS, 'placeholder': 'you@example.com'}),
            'phone_number': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Phone number'}),
            'address': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Street address'}),
            'city': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'City'}),
            'country': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Country'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _strip_help_and_labels(self)

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if email != (self.instance.email or '').lower():
            if User.objects.filter(email__iexact=email).exists():
                raise forms.ValidationError('An account with this email already exists.')
        return email


class PasswordResetRequestForm(forms.Form):
    """Forgot-password email request."""

    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': INPUT_CLASS, 'placeholder': 'you@example.com',
            'autocomplete': 'email', 'autofocus': True,
        }),
        error_messages={
            'required': 'Please enter your email address.',
            'invalid': 'Please enter a valid email address.',
        },
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _strip_help_and_labels(self)

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        # Never reveal whether the email exists — just attach the user if found.
        try:
            user = User.objects.get(email__iexact=email, is_active=True)
            self.cleaned_data['user'] = user
        except User.DoesNotExist:
            self.cleaned_data['user'] = None
        return email


class StyledSetPasswordForm(SetPasswordForm):
    """Reset-confirm form with premium inputs and no Django help text."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['new_password1'].widget = forms.PasswordInput(attrs={
            'class': INPUT_CLASS, 'placeholder': 'New password', 'autocomplete': 'new-password',
        })
        self.fields['new_password2'].widget = forms.PasswordInput(attrs={
            'class': INPUT_CLASS, 'placeholder': 'Confirm new password', 'autocomplete': 'new-password',
        })
        self.error_messages['password_mismatch'] = 'The two passwords don’t match.'
        _strip_help_and_labels(self)
