"""
Subscriber email notifications: a welcome email plus automatic product alerts
(new arrival / restock / discount).

Design notes
------------
* Sending is centralised in `_send_html`
  so every email is auditable from the admin.
* Product alerts are triggered by Django signals (see signals.py) wrapped in
  `transaction.on_commit`, so emails only go out after the product is safely
  committed — never mid-transaction.
* `notify_product` is intentionally a plain function so it can be handed to a
  Celery task untouched once a broker is configured (see tasks.py).
"""

import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────

def _abs_url(path):
    """Build an absolute URL for emails (links must work outside the browser)."""
    return f"{settings.SITE_URL.rstrip('/')}{path}"


def _active_email_subscribers():
    from .models import NewsletterSubscriber
    return (
        NewsletterSubscriber.objects
        .filter(status='active')
        .exclude(email__isnull=True)
        .exclude(email='')
    )


def _format_gnf(amount):
    try:
        return f"{float(amount):,.0f} GNF".replace(',', ' ')
    except (TypeError, ValueError):
        return f"{amount} GNF"


def _send_html(to_email, subject, html, email_type='notification'):
    """Send one HTML email. Returns True on success. (No DB journaling.)"""
    text_body = strip_tags(html)
    message = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[to_email],
    )
    message.attach_alternative(html, 'text/html')

    try:
        message.send()
        return True
    except Exception:  # noqa: BLE001 — log, never raise to caller
        logger.exception("Newsletter email '%s' to %s failed", subject, to_email)
        return False


# ─────────────────────────────────────────────────────────────
# Welcome email
# ─────────────────────────────────────────────────────────────

def send_subscription_welcome(subscriber):
    """Confirmation email sent right after someone subscribes."""
    html = render_to_string('emails/newsletter_welcome.html', {
        'business_name': settings.BUSINESS_NAME,
        'shop_url': _abs_url(reverse('catalog')),
        'site_url': settings.SITE_URL,
    })
    return _send_html(
        subscriber.email,
        f"Welcome to {settings.BUSINESS_NAME}",
        html,
        email_type='welcome',
    )


# ─────────────────────────────────────────────────────────────
# Automatic product alerts
# ─────────────────────────────────────────────────────────────

_KIND_META = {
    'new_arrival': {
        'eyebrow': 'Just dropped',
        'cta': 'Shop the drop',
        'subject': 'New arrival at {business}: {product}',
    },
    'restock': {
        'eyebrow': 'Back in stock',
        'cta': 'Get it before it’s gone',
        'subject': 'Back in stock: {product}',
    },
    'discount': {
        'eyebrow': 'Now on sale',
        'cta': 'Shop the offer',
        'subject': '{discount}% off {product} — limited time',
    },
}


def notify_product(product_id, kind):
    """
    Email every active subscriber about a product event.

    kind ∈ {'new_arrival', 'restock', 'discount'}. Safe to call from a signal
    or a Celery task. Honours settings.PRODUCT_NOTIFICATIONS_ENABLED.
    """
    if not getattr(settings, 'PRODUCT_NOTIFICATIONS_ENABLED', True):
        return 0

    meta = _KIND_META.get(kind)
    if meta is None:
        logger.warning("notify_product called with unknown kind: %s", kind)
        return 0

    from shop.models import Product
    product = (
        Product.objects.select_related('brand', 'category')
        .prefetch_related('images')
        .filter(id=product_id)
        .first()
    )
    if product is None:
        return 0

    image = product.images.first()
    image_url = _abs_url(image.image.url) if image and image.image else ''
    product_url = _abs_url(reverse('product_detail', args=[product.slug]))

    has_discount = product.discount_percent and product.discount_percent > 0
    context = {
        'business_name': settings.BUSINESS_NAME,
        'eyebrow': meta['eyebrow'],
        'cta_label': meta['cta'],
        'product_name': product.name,
        'product_description': (product.description or '')[:240],
        'product_url': product_url,
        'image_url': image_url,
        'brand': product.brand.name if product.brand else '',
        'price': _format_gnf(product.price_gnf),
        'has_discount': bool(has_discount),
        'discount_percent': product.discount_percent,
        'discounted_price': _format_gnf(product.discounted_price) if has_discount else '',
        'site_url': settings.SITE_URL,
    }

    subject = meta['subject'].format(
        business=settings.BUSINESS_NAME,
        product=product.name,
        discount=product.discount_percent,
    )
    html = render_to_string('emails/product_notification.html', context)

    sent = 0
    for subscriber in _active_email_subscribers().iterator():
        if _send_html(subscriber.email, subject, html, email_type='notification'):
            sent += 1

    logger.info("Product alert '%s' for '%s' sent to %d subscribers", kind, product.name, sent)
    return sent
