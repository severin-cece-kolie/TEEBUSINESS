"""
Global business constants for TEEBUSINESS
"""

# ===== BUSINESS CONTACT INFORMATION =====
BUSINESS_PHONE = "+224 623 70 78 33"
BUSINESS_EMAIL = "kseverin189@gmail.com"
BUSINESS_NAME = "TEEBUSINESS"

# ===== CONTACT INFORMATION OBJECT =====
CONTACT_INFO = {
    'phone': BUSINESS_PHONE,
    'email': BUSINESS_EMAIL,
    'business_name': BUSINESS_NAME,
}

# ===== EMAIL TEMPLATES =====
EMAIL_TEMPLATES = {
    'welcome_subject': 'Welcome to TEEBUSINESS',
    'password_reset_subject': 'Reset Your Password - TEEBUSINESS',
    'order_confirmation_subject': 'Order Confirmation - TEEBUSINESS',
    'order_status_subject': 'Order Status Update - TEEBUSINESS',
    'contact_form_subject': 'New Contact Form Submission - TEEBUSINESS',
    'newsletter_subject': 'TEEBUSINESS Newsletter',
}

# ===== SMS TEMPLATES =====
SMS_TEMPLATES = {
    'welcome': f'Welcome to TEEBUSINESS! If you need any help, contact us at {BUSINESS_PHONE} or {BUSINESS_EMAIL}',
    'password_reset': 'Your TEEBUSINESS password reset link is ready. Check your email to secure your account.',
    'order_confirmation': 'Thank you for your order! You will receive updates at {email}. Questions? Contact {phone}',
    'order_status': 'Your TEEBUSINESS order status has been updated. Check your account or contact {phone}',
    'registration': f'Welcome to TEEBUSINESS! Your account is ready. Need help? Call {BUSINESS_PHONE}',
}
