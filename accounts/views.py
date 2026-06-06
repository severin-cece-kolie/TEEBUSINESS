from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.contrib.auth.views import PasswordResetView, PasswordResetConfirmView
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import (
    LoginForm, ProfileForm, RegisterForm, 
    OTPVerificationForm, ResendOTPForm, PasswordResetRequestForm
)
from .email_utils import send_welcome_email, send_password_reset_email
from .models import User
from .utils import (
    generate_otp, send_otp_email, get_client_ip, 
    log_security_event, reset_rate_limit
)


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    form = LoginForm(request, data=request.POST or None)
    
    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        ip_address = get_client_ip(request)
        
        # Record successful login
        user.record_successful_login(ip_address)
        log_security_event(user, 'login_success', request)
        
        # Handle remember-me functionality
        if form.cleaned_data.get('remember_me'):
            request.session.set_expiry(30 * 24 * 60 * 60)  # 30 days
        else:
            request.session.set_expiry(0)  # Browser session
        
        login(request, user)
        
        # Check if email verification is required
        if user.requires_email_verification and not user.is_email_verified:
            messages.warning(request, 'Please verify your email to continue.')
            return redirect('verify_otp')
        
        return redirect(request.GET.get('next') or 'dashboard')
    elif request.method == 'POST':
        # Record failed login attempt
        username = request.POST.get('username')
        ip_address = get_client_ip(request)
        
        try:
            user = User.objects.get(username=username)
            user.record_failed_login(ip_address)
            log_security_event(user, 'login_failed', request, {'username': username})
            
            if user.is_locked():
                log_security_event(user, 'account_locked', request, {'username': username})
                messages.error(request, 'Account temporarily locked due to multiple failed attempts.')
            elif user.failed_login_attempts >= 10:
                messages.error(request, 'Too many failed attempts. Email verification required.')
            else:
                messages.error(request, 'Invalid username or password.')
        except User.DoesNotExist:
            log_security_event(None, 'login_failed', request, {'username': username})
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'accounts/login.html', {'form': form})


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    form = RegisterForm(request.POST or None)
    
    if request.method == 'POST' and form.is_valid():
        # Create user with is_active=False until OTP verification
        user = form.save(commit=False)
        user.is_active = False  # Account inactive until OTP verified
        user.save()
        
        # Generate and send OTP
        otp = generate_otp(user, purpose='email_verification')
        send_otp_email(user, otp, request)
        
        # Log registration
        log_security_event(user, 'otp_verified' if user.is_email_verified else 'otp_failed', request, {'action': 'registration'})
        
        messages.success(request, 'Account created successfully. Please check your email for the verification code.')
        return redirect('verify_otp', user_id=user.id)
    
    return render(request, 'accounts/register.html', {'form': form})


def verify_otp_view(request, user_id=None):
    """View for OTP verification."""
    
    # Get user from session or URL parameter
    if user_id:
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            messages.error(request, 'Invalid user.')
            return redirect('login')
    elif 'pending_verification_user_id' in request.session:
        user_id = request.session['pending_verification_user_id']
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            messages.error(request, 'Invalid user.')
            return redirect('login')
    else:
        messages.error(request, 'No pending verification.')
        return redirect('login')
    
    form = OTPVerificationForm(
        data=request.POST or None,
        user=user,
        purpose='email_verification'
    )
    
    if request.method == 'POST' and form.is_valid():
        # OTP verified successfully
        user.is_active = True
        user.is_email_verified = True
        user.email_verification_date = timezone.now()
        user.requires_email_verification = False
        user.save()
        
        # Clear session
        if 'pending_verification_user_id' in request.session:
            del request.session['pending_verification_user_id']
        
        # Log successful verification
        log_security_event(user, 'otp_verified', request)
        
        # Send welcome email
        send_welcome_email(user, request)
        
        # Auto-login after verification
        login(request, user)
        
        messages.success(request, 'Email verified successfully. Welcome to TEEBUSINESS!')
        return redirect('dashboard')
    
    return render(request, 'accounts/verify_otp.html', {'form': form, 'user': user})


def resend_otp_view(request):
    """View for resending OTP."""
    
    if request.method == 'POST':
        form = ResendOTPForm(request.POST)
        
        if form.is_valid():
            user = form.cleaned_data['user']
            
            # Generate new OTP
            otp = generate_otp(user, purpose='email_verification')
            send_otp_email(user, otp, request)
            
            messages.success(request, 'New verification code sent to your email.')
            return redirect('verify_otp', user_id=user.id)
    else:
        form = ResendOTPForm()
    
    return render(request, 'accounts/resend_otp.html', {'form': form})


def logout_view(request):
    if request.method == 'POST':
        user = request.user
        logout(request)
        messages.success(request, 'You have been logged out.')
        
        if user.is_authenticated:
            log_security_event(user, 'login_success', request, {'action': 'logout'})
    
    return redirect('home')


@login_required(login_url='login')
def dashboard_view(request):
    return render(request, 'accounts/dashboard.html')


@login_required(login_url='login')
def orders_view(request):
    return render(request, 'accounts/orders.html')


@login_required(login_url='login')
def wishlist_view(request):
    return render(request, 'accounts/wishlist.html')


@login_required(login_url='login')
def profile_view(request):
    form = ProfileForm(request.POST or None, instance=request.user)
    
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Profile updated.')
        return redirect('profile')
    
    return render(request, 'accounts/profile.html', {'form': form})


class CustomPasswordResetView(PasswordResetView):
    """Override Django's default password reset to use HTML email templates."""
    template_name = 'accounts/password_reset.html'
    success_url = reverse_lazy('password_reset_done')
    form_class = PasswordResetRequestForm
    
    def form_valid(self, form):
        """Send password reset email using custom HTML template."""
        user = form.cleaned_data.get('user')
        
        if user:
            opts = {
                'use_https': self.request.is_secure(),
                'token_generator': self.token_generator,
                'from_email': self.from_email,
                'email_template_name': self.email_template_name,
                'subject_template_name': self.subject_template_name,
                'request': self.request,
                'extra_email_context': self.extra_email_context,
            }
            
            # Generate reset token and UID
            from django.contrib.auth.tokens import default_token_generator
            from django.utils.http import urlsafe_base64_encode
            from django.utils.encoding import force_bytes
            
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            
            reset_link = self.request.build_absolute_uri(
                reverse_lazy('password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
            )
            
            # Send HTML email instead of default text email
            send_password_reset_email(user, reset_link, self.request)
            
            # Log password reset request
            from .utils import log_security_event
            log_security_event(user, 'password_changed', self.request, {'action': 'reset_requested'})
        
        return super().form_valid(form)


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    """Override default password reset confirm view."""
    template_name = 'accounts/password_reset_confirm.html'
    success_url = reverse_lazy('password_reset_complete')
    
    def form_valid(self, form):
        """Log successful password reset."""
        response = super().form_valid(form)
        
        # Log password reset completion
        from .utils import log_security_event
        log_security_event(self.user, 'password_changed', self.request, {'action': 'reset_completed'})
        
        # Reset failed login attempts after password reset
        self.user.unlock_account()
        
        return response
