"""
Celery task stubs for email campaign delivery.

These run synchronously until Celery + Redis are configured.
To enable async sending:
  1. pip install celery redis
  2. Set CELERY_BROKER_URL in settings.py / .env
  3. Run: celery -A teebusiness_core worker -l info
"""


def send_product_notification_task(product_id, kind):
    """
    Email all active subscribers about a product event
    (kind ∈ 'new_arrival' | 'restock' | 'discount').

    Runs synchronously today. To make it async, decorate with @shared_task and
    call `.delay(product_id, kind)` from communication/signals.py — the body
    here stays identical.
    """
    from communication.notifications import notify_product
    return notify_product(product_id, kind)


def send_email_campaign_task(campaign_id):
    """Send a campaign synchronously (Celery stub)."""
    from communication.models import EmailCampaign, NewsletterSubscriber, CampaignRecipient
    from django.core.mail import EmailMultiAlternatives
    from django.utils import timezone

    try:
        campaign = EmailCampaign.objects.get(id=campaign_id, status='draft')
    except EmailCampaign.DoesNotExist:
        return

    subscribers = NewsletterSubscriber.objects.filter(status='active')
    campaign.total_recipients = subscribers.count()
    campaign.status = 'sending'
    campaign.save(update_fields=['total_recipients', 'status'])

    sent = failed = 0
    for subscriber in subscribers:
        recipient, _ = CampaignRecipient.objects.get_or_create(
            campaign=campaign, subscriber=subscriber
        )
        try:
            msg = EmailMultiAlternatives(
                subject=campaign.subject,
                body=campaign.plain_text_content or '',
                from_email=campaign.sender_email,
                to=[subscriber.email],
            )
            msg.attach_alternative(campaign.html_content, 'text/html')
            msg.send()
            recipient.status = 'sent'
            recipient.sent_at = timezone.now()
            recipient.save(update_fields=['status', 'sent_at'])
            sent += 1
        except Exception as exc:
            recipient.status = 'failed'
            recipient.error_message = str(exc)
            recipient.failed_at = timezone.now()
            recipient.save(update_fields=['status', 'error_message', 'failed_at'])
            failed += 1

    campaign.sent_count = sent
    campaign.failed_count = failed
    campaign.status = 'sent'
    campaign.sent_at = timezone.now()
    campaign.save(update_fields=['sent_count', 'failed_count', 'status', 'sent_at'])
