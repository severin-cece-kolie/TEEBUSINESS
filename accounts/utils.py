"""
Utility functions for OTP generation, verification, and email sending.
"""

import logging
import random
import string
from datetime import timedelta
from django.utils import timezone
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from .models import OTP, LoginSecurityLog

logger = logging.getLogger('accounts')


def generate_otp(user, purpose='email_verification', expiration_minutes=10):
    """
    Generate a 6-digit OTP code for the specified purpose.
    
    Args:
        user: User instance
        purpose: Purpose of OTP (email_verification, password_reset, login_verification)
        expiration_minutes: OTP expiration time in minutes (default: 10)
    
    Returns:
        OTP instance
    """
    # Generate 6-digit OTP
    code = ''.join(random.choices(string.digits, k=6))
    
    # Calculate expiration time
    expires_at = timezone.now() + timedelta(minutes=expiration_minutes)
    
    # Create OTP record
    otp = OTP.objects.create(
        user=user,
        code=code,
        purpose=purpose,
        expires_at=expires_at
    )
    
    return otp


def verify_otp(user, code, purpose='email_verification'):
    """
    Verify an OTP code for the specified purpose.
    
    Args:
        user: User instance
        code: OTP code to verify
        purpose: Purpose of OTP
    
    Returns:
        tuple (is_valid, otp_instance or error_message)
    """
    try:
        # Get the most recent unused OTP for this user and purpose
        otp = OTP.objects.filter(
            user=user,
            code=code,
            purpose=purpose,
            is_used=False
        ).latest('created_at')
        
        # Check if OTP is valid
        if not otp.is_valid():
            if otp.expires_at < timezone.now():
                return False, 'OTP has expired. Please request a new one.'
            if otp.is_used:
                return False, 'OTP has already been used. Please request a new one.'
        
        # Mark OTP as used
        otp.mark_as_used()
        
        # Log successful OTP verification
        LoginSecurityLog.objects.create(
            user=user,
            event_type='otp_verified',
            details={'purpose': purpose}
        )
        
        return True, otp
        
    except OTP.DoesNotExist:
        # Log failed OTP verification
        LoginSecurityLog.objects.create(
            user=user,
            event_type='otp_failed',
            details={'purpose': purpose, 'reason': 'Invalid OTP code'}
        )
        return False, 'Invalid OTP code. Please try again.'


def send_otp_email(user, otp, request=None):
    """
    Send OTP email to user.
    
    Args:
        user: User instance
        otp: OTP instance
        request: Optional request object for building absolute URLs
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        # Build context for email template
        context = {
            'user': user,
            'otp': otp,
            'business_name': settings.BUSINESS_NAME,
            'business_email': settings.BUSINESS_EMAIL,
            'business_phone': settings.BUSINESS_PHONE,
        }
        
        # Render email content
        subject = f'{settings.BUSINESS_NAME} - Your Verification Code'
        html_content = render_to_string('accounts/emails/otp_email.html', context)
        plain_text_content = render_to_string('accounts/emails/otp_email.txt', context)
        
        # Create email
        email = EmailMultiAlternatives(
            subject=subject,
            body=plain_text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
            # This helper writes its own (richer) EmailHistory row below, so tell
            # the LoggingEmailBackend not to journal this message a second time.
            headers={'X-TEE-NoLog': '1'},
        )
        
        # Attach HTML content
        email.attach_alternative(html_content, 'text/html')
        
        # Send email — fail_silently=False so SMTP errors raise and are logged
        # (the previous default swallowed connection/auth errors invisibly).
        logger.info(
            "Sending OTP email to %s via backend=%s host=%s:%s",
            user.email, settings.EMAIL_BACKEND,
            getattr(settings, 'EMAIL_HOST', '-'), getattr(settings, 'EMAIL_PORT', '-'),
        )
        result = email.send(fail_silently=False)

        # Log to email history
        from communication.models import EmailHistory
        EmailHistory.objects.create(
            email_type='otp',
            to_email=user.email,
            from_email=settings.DEFAULT_FROM_EMAIL,
            subject=subject,
            body=html_content,
            status='sent' if result == 1 else 'failed',
            related_user=user,
            sent_at=timezone.now() if result == 1 else None
        )

        if result == 1:
            logger.info("OTP email accepted by the mail server for %s", user.email)
        else:
            logger.error("OTP email send() returned %s (not 1) for %s", result, user.email)
        return result == 1

    except Exception as exc:
        # Detailed, non-silent diagnostics — visible in the PythonAnywhere error log.
        logger.exception(
            "OTP EMAIL FAILED for %s | backend=%s host=%s:%s tls=%s user=%s | %s: %s",
            getattr(user, 'email', '?'), settings.EMAIL_BACKEND,
            getattr(settings, 'EMAIL_HOST', '-'), getattr(settings, 'EMAIL_PORT', '-'),
            getattr(settings, 'EMAIL_USE_TLS', '-'), getattr(settings, 'EMAIL_HOST_USER', '-'),
            type(exc).__name__, exc,
        )
        # Record the failure so it shows in the admin Message History too.
        try:
            from communication.models import EmailHistory
            EmailHistory.objects.create(
                email_type='otp', to_email=getattr(user, 'email', ''),
                from_email=settings.DEFAULT_FROM_EMAIL, subject='OTP verification (FAILED)',
                body=f'{type(exc).__name__}: {exc}', status='failed', related_user=user,
            )
        except Exception:
            pass
        return False


def get_client_ip(request):
    """
    Get the real client IP, honouring Cloudflare and reverse proxies.

    Order of precedence:
      1. CF-Connecting-IP  (set by Cloudflare — the true visitor IP)
      2. X-Forwarded-For   (first hop in the chain)
      3. REMOTE_ADDR       (direct connection)
    """
    cf_ip = request.META.get('HTTP_CF_CONNECTING_IP')
    if cf_ip:
        return cf_ip.strip()

    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()

    return request.META.get('REMOTE_ADDR')


def log_security_event(user, event_type, request=None, details=None):
    """
    Log a security event.
    
    Args:
        user: User instance (can be None)
        event_type: Event type from LoginSecurityLog.EVENT_TYPE_CHOICES
        request: Optional request object
        details: Optional dictionary with event details
    """
    ip_address = None
    user_agent = None
    
    if request:
        ip_address = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
    
    LoginSecurityLog.objects.create(
        user=user,
        event_type=event_type,
        ip_address=ip_address,
        user_agent=user_agent,
        details=details or {}
    )


def cleanup_expired_otps():
    """
    Delete expired OTPs from the database.
    This should be called periodically (e.g., via cron or Celery beat).
    """
    expired_count = OTP.objects.filter(
        expires_at__lt=timezone.now(),
        is_used=False
    ).delete()[0]
    
    return expired_count


def check_rate_limit(request, key, max_attempts=5, window_minutes=1):
    """
    Check if a request is within rate limits.
    
    Args:
        request: HttpRequest object
        key: Unique key for rate limiting (e.g., 'login', 'otp_resend')
        max_attempts: Maximum number of attempts allowed
        window_minutes: Time window in minutes
    
    Returns:
        tuple (is_allowed, remaining_attempts, reset_time)
    """
    from django.core.cache import cache
    
    ip_address = get_client_ip(request)
    cache_key = f'rate_limit:{key}:{ip_address}'
    
    # Get current attempts
    attempts_data = cache.get(cache_key, {'count': 0, 'reset_time': None})
    
    # Check if window has expired
    if attempts_data['reset_time'] and attempts_data['reset_time'] < timezone.now():
        attempts_data = {'count': 0, 'reset_time': None}
    
    # Check if limit exceeded
    if attempts_data['count'] >= max_attempts:
        return False, 0, attempts_data['reset_time']
    
    # Increment counter
    attempts_data['count'] += 1
    
    # Set reset time if first attempt
    if not attempts_data['reset_time']:
        attempts_data['reset_time'] = timezone.now() + timedelta(minutes=window_minutes)
    
    # Store in cache
    cache.set(cache_key, attempts_data, timeout=window_minutes * 60)
    
    remaining_attempts = max_attempts - attempts_data['count']
    return True, remaining_attempts, attempts_data['reset_time']


def reset_rate_limit(request, key):
    """
    Reset rate limit for a specific key.
    
    Args:
        request: HttpRequest object
        key: Rate limit key to reset
    """
    from django.core.cache import cache
    
    ip_address = get_client_ip(request)
    cache_key = f'rate_limit:{key}:{ip_address}'
    cache.delete(cache_key)
