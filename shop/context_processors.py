from django.conf import settings
from django.urls import reverse

CURRENCY_OPTIONS = {
    'EUR': {'symbol': '€', 'label': 'Euro'},
    'USD': {'symbol': '$', 'label': 'US Dollar'},
    'GNF': {'symbol': 'FG', 'label': 'Guinean Franc'},
}


def business_processor(request):
    """Expose business contact + social links to every template."""
    whatsapp_number = settings.WHATSAPP_NUMBER
    # Internal route — the real wa.me URL is built server-side in
    # pages.views.whatsapp_redirect so the number never hits the page source.
    whatsapp_url = reverse('whatsapp_redirect')
    return {
        'business_name': settings.BUSINESS_NAME,
        'business_phone': settings.BUSINESS_PHONE,
        'business_email': settings.BUSINESS_EMAIL,
        'social_tiktok': settings.SOCIAL_TIKTOK,
        'social_facebook': settings.SOCIAL_FACEBOOK,
        'whatsapp_number': whatsapp_number,
        'whatsapp_url': whatsapp_url,
        'whatsapp_tooltip': 'Chat with us on WhatsApp',
    }


def currency_processor(request):
    current_currency = request.session.get('currency', 'GNF')
    if current_currency not in CURRENCY_OPTIONS:
        current_currency = 'GNF'

    return {
        'current_currency': current_currency,
        'current_currency_icon': CURRENCY_OPTIONS[current_currency]['symbol'],
        'available_currencies': CURRENCY_OPTIONS,
        # Replace static/assets/images/background1.jpg with your premium banner image
        'site_banner_image': 'assets/images/background1.jpg',
    }
