from decimal import Decimal, ROUND_HALF_UP

from django import template

register = template.Library()

CURRENCY_RATES = {
    'GNF': Decimal('1'),
    'EUR': Decimal('0.00010869565217391304'),
    'USD': Decimal('0.00011'),
}

CURRENCY_FORMATS = {
    'GNF': ('FG', Decimal('1')),
    'EUR': ('€', Decimal('0.01')),
    'USD': ('$', Decimal('0.01')),
}


@register.filter
def convert_price(value, request):
    if value is None:
        return ""

    current_currency = request.session.get('currency', 'GNF')
    rate = CURRENCY_RATES.get(current_currency, CURRENCY_RATES['GNF'])
    symbol, precision = CURRENCY_FORMATS.get(current_currency, CURRENCY_FORMATS['GNF'])
    converted = (Decimal(str(value)) * rate).quantize(precision, rounding=ROUND_HALF_UP)
    decimal_places = max(0, -precision.as_tuple().exponent)
    formatted = f"{converted:,.{decimal_places}f}"
    return f"{symbol} {formatted}"
