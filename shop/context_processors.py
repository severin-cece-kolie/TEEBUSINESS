CURRENCY_OPTIONS = {
    'EUR': {'symbol': '€', 'label': 'Euro'},
    'USD': {'symbol': '$', 'label': 'US Dollar'},
    'GNF': {'symbol': 'FG', 'label': 'Guinean Franc'},
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
