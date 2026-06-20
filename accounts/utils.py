"""
Utility functions for OTP generation, verification, and email sending.
"""

import hashlib
import logging
import random
import string
from types import SimpleNamespace
from datetime import timedelta
from django.utils import timezone
from django.core.cache import cache
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from .models import LoginSecurityLog

logger = logging.getLogger('accounts')

OTP_MAX_ATTEMPTS = 5


def _otp_cache_key(user, purpose):
    return f'otp:{user.pk}:{purpose}'


def _hash_otp(user, code):
    """Hash the code (salted with SECRET_KEY + user id) so plaintext is never stored."""
    return hashlib.sha256(f'{settings.SECRET_KEY}:{user.pk}:{code}'.encode()).hexdigest()


def generate_otp(user, purpose='email_verification', expiration_minutes=None):
    """
    Create a 6-digit OTP. Only its HASH is kept in the Django cache (auto-expiring) —
    nothing is written to the database. Returns a lightweight object carrying the
    plaintext code (with a ``.code`` attribute) so the email template is unchanged.
    """
    code = ''.join(random.choices(string.digits, k=6))
    ttl = int(expiration_minutes or settings.OTP_EXPIRATION_MINUTES) * 60
    cache.set(_otp_cache_key(user, purpose),
              {'hash': _hash_otp(user, code), 'attempts': 0}, ttl)
    return SimpleNamespace(code=code, purpose=purpose, user=user)


def verify_otp(user, code, purpose='email_verification'):
    """
    Validate a submitted code against the cached hash. One-time use (deleted on
    success), limited attempts, auto-expiring. Returns (is_valid, message).
    """
    key = _otp_cache_key(user, purpose)
    data = cache.get(key)
    if not data:
        return False, 'Votre code a expiré ou est invalide. Veuillez en demander un nouveau.'
    if data.get('attempts', 0) >= OTP_MAX_ATTEMPTS:
        cache.delete(key)
        return False, 'Trop de tentatives. Veuillez demander un nouveau code.'
    if _hash_otp(user, str(code).strip()) == data.get('hash'):
        cache.delete(key)  # one-time use
        log_security_event(user, 'otp_verified', None, {'purpose': purpose})
        return True, 'ok'
    data['attempts'] = data.get('attempts', 0) + 1
    cache.set(key, data, int(settings.OTP_EXPIRATION_MINUTES) * 60)
    log_security_event(user, 'otp_failed', None, {'purpose': purpose})
    return False, 'Code incorrect. Veuillez réessayer.'


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
    """No-op kept for backwards compatibility: OTPs now live in the cache and
    expire automatically, so there is nothing to purge from the database."""
    return 0


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
