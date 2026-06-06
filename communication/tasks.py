"""
Celery tasks for email campaign sending.
In production, these tasks would be executed by Celery workers.
"""

from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from .models import EmailCampaign, CampaignRecipient, EmailHistory, NewsletterSubscriber
import traceback


def send_email_campaign_task(campaign_id):
    """
    Send an email campaign to all recipients.
    This task would be executed by Celery in production.
    """
    try:
        campaign = EmailCampaign.objects.get(id=campaign_id)
        
        if campaign.status != 'sending':
            campaign.status = 'sending'
            campaign.save()
        
        # Get all active subscribers
        recipients = NewsletterSubscriber.objects.filter(status='active')
        campaign.total_recipients = recipients.count()
        campaign.save()
        
        # Create campaign recipients
        for subscriber in recipients:
            recipient, created = CampaignRecipient.objects.get_or_create(
                campaign=campaign,
                subscriber=subscriber,
                defaults={'status': 'pending'}
            )
            
            if created or recipient.status == 'pending':
                # Send email
                success = send_campaign_email(campaign, subscriber)
                
                if success:
                    recipient.status = 'sent'
                    recipient.sent_at = timezone.now()
                    campaign.sent_count += 1
                else:
                    recipient.status = 'failed'
                    recipient.failed_at = timezone.now()
                    campaign.failed_count += 1
                
                recipient.save()
        
        campaign.status = 'sent'
        campaign.sent_at = timezone.now()
        campaign.save()
        
    except Exception as e:
        print(f"Error sending campaign: {str(e)}")
        traceback.print_exc()
        if 'campaign' in locals():
            campaign.status = 'cancelled'
            campaign.save()


def send_campaign_email(campaign, subscriber):
    """
    Send a single campaign email to a subscriber.
    """
    try:
        # Create email with HTML content
        email = EmailMultiAlternatives(
            subject=campaign.subject,
            body=campaign.plain_text_content or campaign.html_content,
            from_email=campaign.from_email,
            to=[subscriber.email],
            reply_to=[campaign.reply_to] if campaign.reply_to else None
        )
        
        # Attach HTML content
        email.attach_alternative(campaign.html_content, 'text/html')
        
        # Send email
        result = email.send()
        
        # Log to email history
        EmailHistory.objects.create(
            email_type='campaign',
            to_email=subscriber.email,
            from_email=campaign.from_email,
            subject=campaign.subject,
            body=campaign.html_content,
            status='sent' if result == 1 else 'failed',
            campaign=campaign,
            sent_at=timezone.now() if result == 1 else None
        )
        
        return result == 1
        
    except Exception as e:
        # Log failure
        EmailHistory.objects.create(
            email_type='campaign',
            to_email=subscriber.email,
            from_email=campaign.from_email,
            subject=campaign.subject,
            body=campaign.html_content,
            status='failed',
            campaign=campaign,
            error_message=str(e)
        )
        return False


def send_notification_email(subscriber, notification_type, context):
    """
    Send automated notification emails (new product, restock, discount, etc.).
    """
    try:
        template_map = {
            'new_product': 'communication/emails/new_product_notification.html',
            'restock': 'communication/emails/restock_notification.html',
            'discount': 'communication/emails/discount_notification.html',
            'campaign': 'communication/emails/campaign_notification.html',
        }
        
        template = template_map.get(notification_type)
        if not template:
            return False
        
        html_content = render_to_string(template, context)
        subject = context.get('subject', 'Notification from TEEBUSINESS')
        
        email = EmailMultiAlternatives(
            subject=subject,
            body=html_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[subscriber.email]
        )
        
        email.attach_alternative(html_content, 'text/html')
        result = email.send()
        
        # Log to email history
        EmailHistory.objects.create(
            email_type='notification',
            to_email=subscriber.email,
            from_email=settings.DEFAULT_FROM_EMAIL,
            subject=subject,
            body=html_content,
            status='sent' if result == 1 else 'failed',
            sent_at=timezone.now() if result == 1 else None
        )
        
        return result == 1
        
    except Exception as e:
        print(f"Error sending notification: {str(e)}")
        return False


def send_welcome_email(subscriber):
    """
    Send welcome email to new subscriber.
    """
    try:
        context = {
            'subscriber': subscriber,
            'business_name': settings.BUSINESS_NAME,
        }
        
        html_content = render_to_string('communication/emails/welcome_email.html', context)
        subject = f'Welcome to {settings.BUSINESS_NAME}!'
        
        email = EmailMultiAlternatives(
            subject=subject,
            body=html_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[subscriber.email]
        )
        
        email.attach_alternative(html_content, 'text/html')
        result = email.send()
        
        # Log to email history
        EmailHistory.objects.create(
            email_type='welcome',
            to_email=subscriber.email,
            from_email=settings.DEFAULT_FROM_EMAIL,
            subject=subject,
            body=html_content,
            status='sent' if result == 1 else 'failed',
            sent_at=timezone.now() if result == 1 else None
        )
        
        return result == 1
        
    except Exception as e:
        print(f"Error sending welcome email: {str(e)}")
        return False
