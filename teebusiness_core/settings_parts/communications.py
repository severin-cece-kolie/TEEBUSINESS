"""Email providers, retry behavior, and SMS provider credentials."""

from .base import env, env_bool, env_int


_EMAIL_BACKEND_ALIASES = {
    'console': 'django.core.mail.backends.console.EmailBackend',
    'smtp': 'django.core.mail.backends.smtp.EmailBackend',
    'brevo': 'communication.email_backends.BrevoApiEmailBackend',
    'dummy': 'django.core.mail.backends.dummy.EmailBackend',
    'filebased': 'django.core.mail.backends.filebased.EmailBackend',
    'locmem': 'django.core.mail.backends.locmem.EmailBackend',
}

_backend_key = env('EMAIL_BACKEND', 'console')
EMAIL_PROVIDER_BACKEND = _EMAIL_BACKEND_ALIASES.get(_backend_key, _backend_key)
EMAIL_BACKEND = 'communication.email_backends.LoggingEmailBackend'
EMAIL_MAX_RETRIES = env_int('EMAIL_MAX_RETRIES', 2)
EMAIL_HTTP_TIMEOUT = env_int('EMAIL_HTTP_TIMEOUT', 20)

BREVO_API_KEY = env('BREVO_API_KEY', '')

EMAIL_HOST = env('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = env_int('EMAIL_PORT', 587)
EMAIL_USE_TLS = env_bool('EMAIL_USE_TLS', True)
EMAIL_HOST_USER = env('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', '').replace(' ', '')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', 'noreply@teebusiness.com')
SERVER_EMAIL = env('SERVER_EMAIL', DEFAULT_FROM_EMAIL)

SMS_ENABLED = env_bool('SMS_ENABLED', False)
TWILIO_ACCOUNT_SID = env('TWILIO_ACCOUNT_SID', '')
TWILIO_AUTH_TOKEN = env('TWILIO_AUTH_TOKEN', '')
TWILIO_PHONE_NUMBER = env('TWILIO_PHONE_NUMBER', '')
