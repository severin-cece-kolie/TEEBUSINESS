from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.contrib.auth.views import PasswordResetView, PasswordResetConfirmView
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.cache import never_cache

from .forms import (
    LoginForm, ProfileForm, RegisterForm,
    OTPVerificationForm, ResendOTPForm, PasswordResetRequestForm,
    StyledSetPasswordForm,
)
from .email_utils import send_welcome_email, send_password_reset_email
from .models import User
from .utils import (
    generate_otp, send_otp_email, get_client_ip,
    log_security_event,
)


def _find_user_by_identifier(identifier):
    """Look up a user by email first (our login identifier), then username."""
    if not identifier:
        return None
    user = User.objects.filter(email__iexact=identifier).first()
    if user is None:
        user = User.objects.filter(username=identifier).first()
    return user


@never_cache
def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    form = LoginForm(request, data=request.POST or None)

    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        ip_address = get_client_ip(request)

        user.record_successful_login(ip_address)
        log_security_event(user, 'login_success', request)

        if form.cleaned_data.get('remember_me'):
            request.session.set_expiry(30 * 24 * 60 * 60)  # 30 days
        else:
            request.session.set_expiry(0)  # Until browser closes

        login(request, user)

        if user.requires_email_verification and not user.is_email_verified:
            return redirect('verify_otp', user_id=user.id)

        # Validate ?next= to prevent open-redirect attacks.
        next_url = request.GET.get('next') or request.POST.get('next')
        if next_url and url_has_allowed_host_and_scheme(
            next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
        ):
            return redirect(next_url)
        return redirect('dashboard')

    elif request.method == 'POST':
        identifier = request.POST.get('username')
        ip_address = get_client_ip(request)
        user = _find_user_by_identifier(identifier)

        if user is not None:
            user.record_failed_login(ip_address)
            log_security_event(user, 'login_failed', request, {'identifier': identifier})
            if user.is_locked():
                log_security_event(user, 'account_locked', request, {'identifier': identifier})

    return render(request, 'accounts/login.html', {'form': form})


@never_cache
def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    form = RegisterForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        user = form.save(commit=False)
        user.is_active = False  # Inactive until OTP verification
        user.save()

        otp = generate_otp(user, purpose='email_verification')
        send_otp_email(user, otp, request)

        request.session['pending_verification_user_id'] = str(user.id)
        messages.success(request, 'We’ve sent a 6-digit code to your email.')
        return redirect('verify_otp', user_id=user.id)

    return render(request, 'accounts/register.html', {'form': form})


@never_cache
def verify_otp_view(request, user_id=None):
    if user_id:
        user = User.objects.filter(id=user_id).first()
    elif 'pending_verification_user_id' in request.session:
        user = User.objects.filter(id=request.session['pending_verification_user_id']).first()
    else:
        user = None

    if user is None:
        messages.error(request, 'Your verification session has expired. Please sign in.')
        return redirect('login')

    form = OTPVerificationForm(
        data=request.POST or None,
        user=user,
        purpose='email_verification',
    )

    if request.method == 'POST' and form.is_valid():
        user.is_active = True
        user.is_email_verified = True
        user.email_verification_date = timezone.now()
        user.requires_email_verification = False
        user.save()

        request.session.pop('pending_verification_user_id', None)
        log_security_event(user, 'otp_verified', request)
        send_welcome_email(user, request)

        # Our EmailBackend is non-default, so be explicit about the backend.
        login(request, user, backend='accounts.backends.EmailBackend')
        return redirect('dashboard')

    return render(request, 'accounts/verify_otp.html', {'form': form, 'user': user})


@never_cache
def resend_otp_view(request):
    form = ResendOTPForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        user = form.cleaned_data['user']
        otp = generate_otp(user, purpose='email_verification')
        send_otp_email(user, otp, request)
        messages.success(request, 'A new code is on its way to your inbox.')
        return redirect('verify_otp', user_id=user.id)

    return render(request, 'accounts/resend_otp.html', {'form': form})


@never_cache
def community_signup(request):
    """
    Lead-capture from the 'Join Community' popup. Creates an active account
    and logs the visitor in immediately, without leaving the current page.
    Returns JSON so the popup can close and the user keeps browsing.
    """
    import json
    from django.http import JsonResponse
    from django.core.validators import validate_email
    from django.core.exceptions import ValidationError

    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Method not allowed.'}, status=405)

    try:
        data = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid request.'}, status=400)

    email = (data.get('email') or '').strip().lower()
    full_name = (data.get('full_name') or '').strip()

    try:
        validate_email(email)
    except ValidationError:
        return JsonResponse({'status': 'error', 'message': 'Please enter a valid email address.'}, status=400)

    first_name, _, last_name = full_name.partition(' ')

    existing = User.objects.filter(email__iexact=email).first()
    if existing is not None:
        # Already registered — don't duplicate. Log them in only if already
        # authenticated isn't possible here, so just acknowledge.
        if not request.user.is_authenticated and existing.is_active:
            login(request, existing, backend='accounts.backends.EmailBackend')
        return JsonResponse({'status': 'success', 'message': 'Welcome back to the TEEBUSINESS community.'})

    user = User(
        username=email,
        email=email,
        first_name=first_name,
        last_name=last_name,
        is_active=True,            # No OTP gate for lead capture
        is_email_verified=False,   # They can verify / set a password later
    )
    from django.utils.crypto import get_random_string
    user.set_password(get_random_string(20))
    user.save()

    # Also capture them as a newsletter subscriber (best-effort).
    try:
        from communication.models import NewsletterSubscriber
        if not NewsletterSubscriber.objects.filter(email__iexact=email).exists():
            NewsletterSubscriber.objects.create(
                full_name=full_name or email.split('@')[0],
                email=email,
                source='website',
                status='active',
            )
    except Exception:
        pass

    login(request, user, backend='accounts.backends.EmailBackend')
    try:
        send_welcome_email(user, request)
    except Exception:
        pass

    return JsonResponse({'status': 'success', 'message': 'Welcome to the TEEBUSINESS community.'})


def logout_view(request):
    if request.method == 'POST':
        user = request.user if request.user.is_authenticated else None
        if user:
            log_security_event(user, 'logout', request)
        logout(request)
    return redirect('home')


@login_required(login_url='login')
def dashboard_view(request):
    return render(request, 'accounts/dashboard.html')


@login_required(login_url='login')
def orders_view(request):
    from cart.models import Order
    orders = (Order.objects
              .filter(user=request.user)
              .prefetch_related('items')
              .order_by('-created_at'))
    return render(request, 'accounts/orders.html', {'orders': orders})


@login_required(login_url='login')
def wishlist_view(request):
    return render(request, 'accounts/wishlist.html')


@login_required(login_url='login')
def change_password_view(request):
    from django.contrib.auth import update_session_auth_hash
    from .forms import StyledPasswordChangeForm

    form = StyledPasswordChangeForm(user=request.user, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        update_session_auth_hash(request, user)  # stay logged in
        log_security_event(user, 'password_changed', request, {'action': 'changed_in_account'})
        messages.success(request, 'Your password has been updated.')
        return redirect('profile')
    return render(request, 'accounts/change_password.html', {'form': form})


@login_required(login_url='login')
def profile_view(request):
    form = ProfileForm(request.POST or None, instance=request.user)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Your details have been updated.')
        return redirect('profile')

    return render(request, 'accounts/profile.html', {'form': form})


@method_decorator(never_cache, name='dispatch')
class CustomPasswordResetView(PasswordResetView):
    """Sends the reset link via our branded HTML email template."""
    template_name = 'accounts/password_reset.html'
    success_url = reverse_lazy('password_reset_done')
    form_class = PasswordResetRequestForm

    def form_valid(self, form):
        user = form.cleaned_data.get('user')

        if user:
            from django.contrib.auth.tokens import default_token_generator
            from django.utils.http import urlsafe_base64_encode
            from django.utils.encoding import force_bytes

            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            reset_link = self.request.build_absolute_uri(
                reverse_lazy('password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
            )

            send_password_reset_email(user, reset_link, self.request)
            log_security_event(user, 'password_changed', self.request, {'action': 'reset_requested'})

        # Skip Django's default email machinery; redirect to the "done" page.
        from django.http import HttpResponseRedirect
        return HttpResponseRedirect(self.get_success_url())


@method_decorator(never_cache, name='dispatch')
class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    """Set a new password from the emailed link."""
    template_name = 'accounts/password_reset_confirm.html'
    success_url = reverse_lazy('password_reset_complete')
    form_class = StyledSetPasswordForm

    def form_valid(self, form):
        response = super().form_valid(form)
        log_security_event(self.user, 'password_changed', self.request, {'action': 'reset_completed'})
        self.user.unlock_account()
        return response
