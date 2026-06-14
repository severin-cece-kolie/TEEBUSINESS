"""
Middleware for rate limiting and brute-force protection.
"""

from django.http import JsonResponse
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta
import time


class RateLimitMiddleware:
    """
    Middleware to implement rate limiting on login and sensitive endpoints.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # Rate limit settings from environment or defaults
        self.max_login_attempts = int(getattr(settings, 'MAX_LOGIN_ATTEMPTS', 5))
        self.lockout_duration = int(getattr(settings, 'LOCKOUT_DURATION', 900))  # 15 minutes
        self.otp_resend_limit = int(getattr(settings, 'OTP_RESEND_LIMIT', 5))
        self.otp_resend_cooldown = int(getattr(settings, 'OTP_RESEND_COOLDOWN_MINUTES', 2))
    
    def __call__(self, request):
        # Check rate limits for sensitive endpoints
        if request.path in ['/login/', '/api/login/', '/register/', '/api/register/']:
            self.check_login_rate_limit(request)
        
        if request.path in ['/accounts/resend-otp/', '/api/resend-otp/']:
            self.check_otp_resend_rate_limit(request)
        
        response = self.get_response(request)
        return response
    
    def check_login_rate_limit(self, request):
        """
        Check and enforce login rate limiting.
        """
        if request.method != 'POST':
            return
        
        # Get client IP
        ip_address = self.get_client_ip(request)
        
        # Check cache for rate limit info
        cache_key = f'login_attempts:{ip_address}'
        attempts_data = cache.get(cache_key, {'count': 0, 'lockout_until': None})
        
        # Check if IP is locked out
        if attempts_data['lockout_until'] and attempts_data['lockout_until'] > timezone.now():
            remaining_seconds = int((attempts_data['lockout_until'] - timezone.now()).total_seconds())
            raise RateLimitException(
                f'Too many login attempts. Please try again in {remaining_seconds} seconds.',
                retry_after=remaining_seconds
            )
        
        # Reset counter if lockout period has passed
        if attempts_data['lockout_until'] and attempts_data['lockout_until'] <= timezone.now():
            attempts_data = {'count': 0, 'lockout_until': None}
        
        # Increment counter on POST request
        attempts_data['count'] += 1
        
        # Check if limit exceeded
        if attempts_data['count'] >= self.max_login_attempts:
            attempts_data['lockout_until'] = timezone.now() + timedelta(seconds=self.lockout_duration)
            cache.set(cache_key, attempts_data, timeout=self.lockout_duration)
            raise RateLimitException(
                f'Too many login attempts. Account locked for {self.lockout_duration // 60} minutes.',
                retry_after=self.lockout_duration
            )
        
        # Store in cache with appropriate timeout
        cache.set(cache_key, attempts_data, timeout=self.lockout_duration)
    
    def check_otp_resend_rate_limit(self, request):
        """
        Check and enforce OTP resend rate limiting.
        """
        if request.method != 'POST':
            return
        
        ip_address = self.get_client_ip(request)
        cache_key = f'otp_resend:{ip_address}'
        
        # Get last resend time
        last_resend = cache.get(cache_key)
        
        if last_resend:
            time_since_last = (timezone.now() - last_resend).total_seconds()
            cooldown_remaining = self.otp_resend_cooldown * 60 - time_since_last
            
            if cooldown_remaining > 0:
                raise RateLimitException(
                    f'Please wait {int(cooldown_remaining)} seconds before requesting another OTP.',
                    retry_after=int(cooldown_remaining)
                )
        
        # Update last resend time
        cache.set(cache_key, timezone.now(), timeout=self.otp_resend_cooldown * 60)
    
    def get_client_ip(self, request):
        """Real client IP, honouring Cloudflare (CF-Connecting-IP) and proxies."""
        cf_ip = request.META.get('HTTP_CF_CONNECTING_IP')
        if cf_ip:
            return cf_ip.strip()
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')


class RateLimitException(Exception):
    """Custom exception for rate limit violations."""
    
    def __init__(self, message, retry_after=None):
        self.message = message
        self.retry_after = retry_after
        super().__init__(message)


class SecurityHeadersMiddleware:
    """
    Middleware to add security headers to all responses.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Add security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'

        # Content-Security-Policy (Django 5.2 has no native setting).
        csp = getattr(settings, 'CONTENT_SECURITY_POLICY', '')
        if csp and 'Content-Security-Policy' not in response:
            response['Content-Security-Policy'] = csp
        
        # HSTS header (only in production with HTTPS)
        if not settings.DEBUG:
            response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        return response


class LoginAttemptMiddleware:
    """
    Middleware to track login attempts and detect suspicious activity.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Process request
        response = self.get_response(request)
        
        # Track login attempts
        if request.path in ['/login/', '/api/login/'] and request.method == 'POST':
            self.track_login_attempt(request, response)
        
        return response
    
    def track_login_attempt(self, request, response):
        """
        Track login attempt and detect suspicious activity.
        """
        from accounts.models import LoginSecurityLog
        from accounts.utils import get_client_ip
        
        ip_address = get_client_ip(request)
        username = request.POST.get('username', '')
        
        # Determine if login was successful
        is_success = response.status_code == 302 and '/dashboard/' in response.get('Location', '')
        
        if is_success:
            # Log successful login
            if request.user.is_authenticated:
                LoginSecurityLog.objects.create(
                    user=request.user,
                    event_type='login_success',
                    ip_address=ip_address,
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    details={'username': username}
                )
        else:
            # Log failed login
            LoginSecurityLog.objects.create(
                event_type='login_failed',
                username_attempted=username,
                ip_address=ip_address,
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                details={'status_code': response.status_code}
            )
            
            # Check for suspicious activity (multiple failed attempts from same IP)
            recent_failures = LoginSecurityLog.objects.filter(
                event_type='login_failed',
                ip_address=ip_address,
                created_at__gte=timezone.now() - timedelta(minutes=10)
            ).count()
            
            if recent_failures >= 10:
                # Log suspicious activity
                LoginSecurityLog.objects.create(
                    event_type='suspicious_activity',
                    ip_address=ip_address,
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    details={
                        'reason': 'Multiple failed login attempts',
                        'attempts': recent_failures,
                        'timeframe': '10 minutes'
                    }
                )


class RateLimitExceptionHandler:
    """
    Middleware to handle rate limit exceptions and return appropriate responses.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        try:
            return self.get_response(request)
        except RateLimitException as e:
            return JsonResponse(
                {
                    'error': 'rate_limit_exceeded',
                    'message': e.message,
                    'retry_after': e.retry_after
                },
                status=429
            )
