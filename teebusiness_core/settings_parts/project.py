"""TEEBUSINESS checkout, notifications, business data, cache, and limits."""

from .base import env, env_bool, env_float, env_int


SITE_URL = env('SITE_URL', 'http://localhost:8000')

TAX_RATE_PERCENT = env_float('TAX_RATE_PERCENT', 0)
USD_TO_GNF = env_int('USD_TO_GNF', 9100)
SHIPPING_DEFAULT_ZONE = 'conakry'
SHIPPING_ZONES = {
    'conakry': {
        'label': 'Conakry',
        'gnf': env_int('SHIP_CONAKRY_GNF', 15000),
    },
    'guinea': {
        'label': 'Intérieur de la Guinée',
        'gnf': env_int('SHIP_GUINEA_GNF', 20000),
    },
    'international': {
        'label': 'International',
        'usd': env_int('SHIP_INTL_USD', 10),
    },
}
SHIPPING_COST_GNF = SHIPPING_ZONES['conakry']['gnf']

PRODUCT_NOTIFICATIONS_ENABLED = env_bool('PRODUCT_NOTIFICATIONS_ENABLED', True)

BUSINESS_PHONE = env('BUSINESS_PHONE', '+224 623 70 78 33')
BUSINESS_EMAIL = env('BUSINESS_EMAIL', 'supportteebusiness@gmail.com')
BUSINESS_NAME = env('BUSINESS_NAME', 'TEEBUSINESS')

SOCIAL_TIKTOK = env('SOCIAL_TIKTOK', 'https://www.tiktok.com/@teebusines')
SOCIAL_FACEBOOK = env(
    'SOCIAL_FACEBOOK',
    'https://www.facebook.com/share/17Yxep5woR/?mibextid=wwXIfr',
)
WHATSAPP_NUMBER = env(
    'WHATSAPP_NUMBER',
    ''.join(ch for ch in BUSINESS_PHONE if ch.isdigit()),
)
WHATSAPP_MESSAGE = env(
    'WHATSAPP_MESSAGE',
    'Hello, I would like information about your products.',
)

RATELIMIT_ENABLE = env_bool('RATELIMIT_ENABLE', True)
MAX_LOGIN_ATTEMPTS = env_int('MAX_LOGIN_ATTEMPTS', 5)
LOCKOUT_DURATION = env_int('LOCKOUT_DURATION', 900)
REQUIRE_EMAIL_VERIFICATION_ATTEMPTS = env_int(
    'REQUIRE_EMAIL_VERIFICATION_ATTEMPTS',
    10,
)

OTP_EXPIRATION_MINUTES = env_int('OTP_EXPIRATION_MINUTES', 10)
OTP_RESEND_LIMIT = env_int('OTP_RESEND_LIMIT', 5)
OTP_RESEND_COOLDOWN_MINUTES = env_int('OTP_RESEND_COOLDOWN_MINUTES', 2)

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'teebusiness-cache',
    }
}
