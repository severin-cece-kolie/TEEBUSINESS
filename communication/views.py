import json

from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .models import NewsletterSubscriber
from .notifications import send_subscription_welcome


def _ok(message):
    return JsonResponse({'status': 'success', 'message': message})


def _err(message, code=400):
    return JsonResponse({'status': 'error', 'message': message}, status=code)


@require_POST
def newsletter_subscribe(request):
    """
    Subscribe a visitor from the footer form (JSON API).

    Accepts a single "Email OR Phone" value (the frontend splits it into
    `email` / `phone`). CSRF-protected: the footer JS sends X-CSRFToken.
    """
    try:
        data = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return _err('Invalid request format.')

    email = (data.get('email') or '').strip().lower()
    phone = (data.get('phone') or '').strip()
    source = (data.get('source') or 'website').strip()[:20] or 'website'

    if not email and not phone:
        return _err('Please enter your email or phone number.')

    # Validate the email format when one is supplied.
    if email:
        try:
            validate_email(email)
        except ValidationError:
            return _err('Please enter a valid email address.')

    # ----- Duplicate handling (case-insensitive) -----
    existing = None
    if email:
        existing = NewsletterSubscriber.objects.filter(email__iexact=email).first()
    if existing is None and phone:
        existing = NewsletterSubscriber.objects.filter(phone_number=phone).first()

    if existing is not None:
        if existing.status == 'active':
            return _ok('You’re already on the list — thank you!')
        existing.status = 'active'
        existing.source = source
        if email and not existing.email:
            existing.email = email
        if phone and not existing.phone_number:
            existing.phone_number = phone
        existing.save()
        return _ok('Welcome back — your subscription is active again.')

    # ----- Create a new subscriber -----
    subscriber = NewsletterSubscriber.objects.create(
        full_name=(email.split('@')[0] if email else phone),
        email=email or None,
        phone_number=phone or None,
        source=source,
        status='active',  # Footer opt-in is single-step
    )

    # Best-effort confirmation email (never block the response on email issues).
    if subscriber.email:
        try:
            send_subscription_welcome(subscriber)
        except Exception:
            pass

    return _ok('Thank you for subscribing — check your inbox for new drops!')
