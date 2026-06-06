"""
Email sending utilities for TEEBUSINESS.

Handles sending transactional and marketing emails with HTML templates.
"""

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.urls import reverse
import logging

logger = logging.getLogger(__name__)


def get_site_url(request=None):
    """Get the base site URL."""
    if request:
        return request.build_absolute_uri('/').rstrip('/')
    return settings.SITE_URL if hasattr(settings, 'SITE_URL') else 'https://teebusiness.com'


def send_welcome_email(user, request=None):
    """
    Send welcome email to newly registered user.
    
    Args:
        user: User instance
        request: Optional request object for building URLs
    """
    try:
        site_url = get_site_url(request)
        
        context = {
            'user': user,
            'site_url': site_url,
        }
        
        html_message = render_to_string('emails/welcome_email.html', context)
        
        email = EmailMultiAlternatives(
            subject='Welcome to TEEBUSINESS',
            body='Welcome to TEEBUSINESS!',
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
        )
        email.attach_alternative(html_message, "text/html")
        email.send()
        
        logger.info(f"Welcome email sent to {user.email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send welcome email to {user.email}: {str(e)}")
        return False


def send_password_reset_email(user, reset_link, request=None):
    """
    Send password reset email.
    
    Args:
        user: User instance
        reset_link: Full URL to password reset link
        request: Optional request object for building URLs
    """
    try:
        context = {
            'user': user,
            'reset_link': reset_link,
        }
        
        html_message = render_to_string('emails/password_reset_email.html', context)
        
        email = EmailMultiAlternatives(
            subject='Reset Your Password - TEEBUSINESS',
            body='Click the link in the email to reset your password.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
        )
        email.attach_alternative(html_message, "text/html")
        email.send()
        
        logger.info(f"Password reset email sent to {user.email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send password reset email to {user.email}: {str(e)}")
        return False


def send_order_confirmation_email(order, request=None):
    """
    Send order confirmation email.
    
    Args:
        order: Order instance (must have user, items relationship)
        request: Optional request object for building URLs
    """
    try:
        site_url = get_site_url(request)
        
        context = {
            'order': order,
            'site_url': site_url,
        }
        
        html_message = render_to_string('emails/order_confirmation_email.html', context)
        
        email = EmailMultiAlternatives(
            subject=f'Order Confirmation - TEEBUSINESS (#{order.order_number})',
            body=f'Your order {order.order_number} has been confirmed.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[order.user.email],
        )
        email.attach_alternative(html_message, "text/html")
        email.send()
        
        logger.info(f"Order confirmation email sent to {order.user.email} for order {order.order_number}")
        return True
    except Exception as e:
        logger.error(f"Failed to send order confirmation email: {str(e)}")
        return False


def send_order_status_email(order, status, tracking_number=None, request=None):
    """
    Send order status update email.
    
    Args:
        order: Order instance
        status: Order status (processing, shipped, delivered, etc.)
        tracking_number: Optional tracking number
        request: Optional request object for building URLs
    """
    try:
        site_url = get_site_url(request)
        
        context = {
            'order': order,
            'status': status,
            'tracking_number': tracking_number,
            'site_url': site_url,
        }
        
        html_message = render_to_string('emails/order_status_email.html', context)
        
        status_text = {
            'processing': 'Being Processed',
            'shipped': 'Shipped',
            'delivered': 'Delivered',
            'cancelled': 'Cancelled',
        }.get(status, 'Updated')
        
        email = EmailMultiAlternatives(
            subject=f'Order Status Update - {status_text}',
            body=f'Your order status has been updated to {status_text}.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[order.user.email],
        )
        email.attach_alternative(html_message, "text/html")
        email.send()
        
        logger.info(f"Order status email ({status}) sent to {order.user.email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send order status email: {str(e)}")
        return False


def send_contact_form_email(full_name, email, phone, subject, message, request=None):
    """
    Send contact form submission email to admin.
    
    Args:
        full_name: Sender's full name
        email: Sender's email
        phone: Sender's phone number
        subject: Message subject
        message: Message body
        request: Optional request object for building URLs
    """
    try:
        context = {
            'full_name': full_name,
            'email': email,
            'phone': phone,
            'subject': subject,
            'message': message,
        }
        
        html_message = render_to_string('emails/contact_form_email.html', context)
        
        admin_email = settings.DEFAULT_FROM_EMAIL
        
        email_obj = EmailMultiAlternatives(
            subject=f'New Contact Form Submission - {subject}',
            body=f'New contact form submission from {full_name}',
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[admin_email],
            reply_to=[email],
        )
        email_obj.attach_alternative(html_message, "text/html")
        email_obj.send()
        
        logger.info(f"Contact form email received from {email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send contact form email: {str(e)}")
        return False


def send_newsletter_email(user, featured_items=None, request=None):
    """
    Send newsletter email to user.
    
    Args:
        user: User instance
        featured_items: Optional list of featured product items
        request: Optional request object for building URLs
    """
    try:
        site_url = get_site_url(request)
        
        context = {
            'user': user,
            'site_url': site_url,
            'featured_items': featured_items or [],
        }
        
        html_message = render_to_string('emails/newsletter_email.html', context)
        
        email = EmailMultiAlternatives(
            subject='TEEBUSINESS Newsletter - Exclusive Offers Inside',
            body='Check out this week\'s featured items and exclusive offers.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
        )
        email.attach_alternative(html_message, "text/html")
        email.send()
        
        logger.info(f"Newsletter email sent to {user.email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send newsletter email to {user.email}: {str(e)}")
        return False


def send_batch_newsletter(user_list, featured_items=None, request=None):
    """
    Send newsletter email to multiple users.
    
    Args:
        user_list: List of User instances
        featured_items: Optional list of featured product items
        request: Optional request object for building URLs
    
    Returns:
        Tuple of (success_count, total_count)
    """
    success_count = 0
    total_count = len(user_list)
    
    for user in user_list:
        if send_newsletter_email(user, featured_items, request):
            success_count += 1
    
    logger.info(f"Newsletter batch send: {success_count}/{total_count} successful")
    return success_count, total_count
