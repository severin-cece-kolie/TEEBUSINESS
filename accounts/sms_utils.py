"""
SMS sending utilities for TEEBUSINESS using Twilio.

Handles sending transactional and marketing SMS messages.
"""

from django.conf import settings
import logging

logger = logging.getLogger(__name__)

try:
    from twilio.rest import Client
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False
    logger.warning("Twilio SDK not installed. SMS functionality disabled. Install with: pip install twilio")


def get_sms_client():
    """Get Twilio client instance."""
    if not TWILIO_AVAILABLE:
        return None
    
    account_sid = settings.TWILIO_ACCOUNT_SID
    auth_token = settings.TWILIO_AUTH_TOKEN
    
    if not account_sid or not auth_token:
        logger.warning("Twilio credentials not configured. SMS disabled.")
        return None
    
    try:
        return Client(account_sid, auth_token)
    except Exception as e:
        logger.error(f"Failed to initialize Twilio client: {str(e)}")
        return None


def send_sms(phone_number, message):
    """
    Send SMS message via Twilio.
    
    Args:
        phone_number: Recipient phone number (international format: +224xxxxxxxxx)
        message: SMS message text
    
    Returns:
        bool: True if sent successfully, False otherwise
    """
    if not TWILIO_AVAILABLE:
        logger.warning("Twilio not installed - cannot send SMS")
        return False
    
    if not settings.SMS_ENABLED:
        logger.info(f"SMS disabled - skipping sms to {phone_number}")
        return False
    
    client = get_sms_client()
    if not client:
        return False
    
    try:
        msg = client.messages.create(
            body=message,
            from_=settings.TWILIO_PHONE_NUMBER,
            to=phone_number,
        )
        logger.info(f"SMS sent successfully to {phone_number}. SID: {msg.sid}")
        return True
    except Exception as e:
        logger.error(f"Failed to send SMS to {phone_number}: {str(e)}")
        return False


def send_welcome_sms(user, request=None):
    """
    Send welcome SMS to newly registered user.
    
    Args:
        user: User instance with phone field (if available)
        request: Optional request object
    
    Returns:
        bool: True if sent successfully
    """
    if not hasattr(user, 'phone') or not user.phone:
        logger.info(f"User {user.email} has no phone number - skipping welcome SMS")
        return False
    
    message = f"Welcome to TEEBUSINESS! For support, call +224 623 70 78 33. Start shopping: https://teebusiness.com"
    return send_sms(user.phone, message)


def send_password_reset_sms(user, reset_link, request=None):
    """
    Send password reset SMS to user.
    
    Args:
        user: User instance with phone field
        reset_link: Full URL to password reset link
        request: Optional request object
    
    Returns:
        bool: True if sent successfully
    """
    if not hasattr(user, 'phone') or not user.phone:
        logger.info(f"User {user.email} has no phone number - skipping password reset SMS")
        return False
    
    message = f"TEEBUSINESS: Reset your password here (expires in 24h): {reset_link}"
    return send_sms(user.phone, message)


def send_order_confirmation_sms(order, request=None):
    """
    Send order confirmation SMS.
    
    Args:
        order: Order instance (must have user, order_number)
        request: Optional request object
    
    Returns:
        bool: True if sent successfully
    """
    if not hasattr(order.user, 'phone') or not order.user.phone:
        logger.info(f"User {order.user.email} has no phone number - skipping order SMS")
        return False
    
    message = f"TEEBUSINESS: Order #{order.order_number} confirmed! Total: ${order.total_amount}. Track here: https://teebusiness.com/accounts/orders/"
    return send_sms(order.user.phone, message)


def send_order_status_sms(order, status, tracking_number=None, request=None):
    """
    Send order status update SMS.
    
    Args:
        order: Order instance
        status: Order status (processing, shipped, delivered, etc.)
        tracking_number: Optional tracking number
        request: Optional request object
    
    Returns:
        bool: True if sent successfully
    """
    if not hasattr(order.user, 'phone') or not order.user.phone:
        logger.info(f"User {order.user.email} has no phone number - skipping status SMS")
        return False
    
    status_text = {
        'processing': 'is being prepared',
        'shipped': 'has been shipped',
        'delivered': 'has been delivered',
        'cancelled': 'has been cancelled',
    }.get(status, f'is {status}')
    
    message = f"TEEBUSINESS: Order #{order.order_number} {status_text}."
    if tracking_number:
        message += f" Tracking: {tracking_number}"
    
    return send_sms(order.user.phone, message)


def send_promotional_sms(phone_number, message):
    """
    Send promotional SMS message.
    
    Args:
        phone_number: Recipient phone number
        message: Promotional message text (max 160 chars recommended)
    
    Returns:
        bool: True if sent successfully
    """
    if len(message) > 160:
        logger.warning(f"SMS message too long ({len(message)} chars). Truncating to 160.")
        message = message[:157] + "..."
    
    return send_sms(phone_number, message)


def send_batch_promotional_sms(phone_list, message):
    """
    Send promotional SMS to multiple recipients.
    
    Args:
        phone_list: List of phone numbers
        message: Promotional message
    
    Returns:
        Tuple of (success_count, total_count)
    """
    success_count = 0
    total_count = len(phone_list)
    
    if not TWILIO_AVAILABLE or not settings.SMS_ENABLED:
        logger.warning("SMS not available - batch send skipped")
        return 0, total_count
    
    for phone in phone_list:
        try:
            if send_promotional_sms(phone, message):
                success_count += 1
        except Exception as e:
            logger.error(f"Error sending to {phone}: {str(e)}")
    
    logger.info(f"Batch SMS send: {success_count}/{total_count} successful")
    return success_count, total_count


def get_sms_usage():
    """
    Get SMS usage statistics from Twilio account.
    
    Returns:
        dict: SMS usage data or empty dict if unavailable
    """
    client = get_sms_client()
    if not client:
        return {}
    
    try:
        messages = client.messages.list(limit=1)
        return {
            'total_messages': len(list(messages)),
            'status': 'available'
        }
    except Exception as e:
        logger.error(f"Failed to fetch SMS usage: {str(e)}")
        return {'status': 'unavailable', 'error': str(e)}
