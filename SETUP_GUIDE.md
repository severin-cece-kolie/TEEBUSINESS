# TEEBUSINESS Phase 2 - Email & SMS System Setup Guide

## Installation & Configuration

### 1. Install Required Package
```bash
pip install twilio
```

### 2. Environment Variables Setup

Create a `.env` file in the project root or add these to your environment:

```env
# Gmail SMTP Configuration (for email sending)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=kseverin189@gmail.com
EMAIL_HOST_PASSWORD=your_app_password_here
DEFAULT_FROM_EMAIL=kseverin189@gmail.com

# Twilio SMS Configuration (optional, for SMS)
SMS_ENABLED=True
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=+1234567890

# Business Contact
BUSINESS_PHONE=+224 623 70 78 33
BUSINESS_EMAIL=kseverin189@gmail.com
```

### 3. Gmail App Password Setup

If using Gmail, you need an App Password (not regular password):
1. Go to myaccount.google.com/apppasswords
2. Select "Mail" and "Windows Computer" (or your OS)
3. Generate password and copy it
4. Use this password for EMAIL_HOST_PASSWORD

### 4. Twilio Setup (Optional)

For SMS functionality:
1. Sign up at twilio.com
2. Get Account SID and Auth Token from dashboard
3. Get a Twilio phone number
4. Set SMS_ENABLED=True in environment

---

## Testing the Email System

### Test 1: User Registration Welcome Email

**In Development (Console Backend):**
```
1. Go to /account/register/
2. Create a new account
3. Check Django console output - email content will be displayed
4. Verify "Welcome to TEEBUSINESS" email content appears
```

**In Production (SMTP):**
```
1. Register a user
2. Check user's inbox for welcome email
3. Email should have professional HTML layout with feature list
```

### Test 2: Password Reset Email

**In Development:**
```
1. Go to /account/password-reset/
2. Enter registered user's email
3. Django console will show password reset email content
4. Verify reset link is formatted correctly
```

**In Production:**
```
1. Request password reset
2. Check email inbox for reset link
3. Click link and verify it works
4. Set new password and login with new password
```

### Test 3: Contact Form Email

```
1. Go to /contact/
2. Fill out form with test data
3. Submit form
4. Admin should receive email notification at kseverin189@gmail.com
5. Verify email has sender details clearly displayed
```

### Test 4: Newsletter Email

**From Python Shell:**
```python
from django.contrib.auth.models import User
from accounts.email_utils import send_newsletter_email

user = User.objects.first()
send_newsletter_email(user)
# Check console output or email
```

---

## Testing the SMS System

### Test 1: Verify Twilio Configuration

**From Python Shell:**
```python
from accounts.sms_utils import get_sms_client

client = get_sms_client()
if client:
    print("✓ Twilio is configured correctly")
else:
    print("✗ Twilio not configured - check environment variables")
```

### Test 2: Send Test SMS

```python
from accounts.sms_utils import send_sms

# Replace with actual phone number
result = send_sms("+224623707833", "Test SMS from TEEBUSINESS")
if result:
    print("✓ SMS sent successfully")
else:
    print("✗ Failed to send SMS")
```

### Test 3: Check SMS Usage

```python
from accounts.sms_utils import get_sms_usage

usage = get_sms_usage()
print(usage)
```

---

## Testing Contact Info Integration

### Test 1: Footer Links

```
1. Visit any page (home, shop, etc.)
2. Scroll to footer
3. Verify Contact column appears (5th column on desktop)
4. Click phone link - should dial +224 623 70 78 33 (tel: link)
5. Click email link - should open email client to kseverin189@gmail.com
6. Click WhatsApp link - should open WhatsApp with +224 623 70 78 33
```

### Test 2: Contact Page

```
1. Click "Contact Us" in footer or navigation
2. Verify phone number is +224 623 70 78 33
3. Verify email is kseverin189@gmail.com
4. Test all contact method links (tel, mailto, WhatsApp)
5. Fill contact form and submit
6. Verify admin receives notification email
```

---

## Admin Communication Center

### Accessing Communications Dashboard

1. Go to Django Admin: /admin/
2. Navigate to Communications section (in development, access via custom URL)
3. Available actions:
   - **Send Newsletter** - Send to selected users
   - **Send Promotional Email** - Custom email with subject/message
   - **Send Promotional SMS** - Custom SMS (max 160 chars)
   - **Message History** - View sent messages

### Test Newsletter Sending

```
1. Go to Communications > Send Newsletter
2. Select 1-2 test users
3. Click "Send Newsletter"
4. Verify success message shows in admin
5. Check user's email for newsletter
```

### Test SMS Campaign

```
1. Go to Communications > Send Promotional SMS
2. Select users (only those with phone numbers)
3. Enter promotional message (max 160 chars)
4. Click "Send"
5. Verify SMS count matches
6. Check user's phone for SMS delivery
```

---

## Responsive Design Testing

### Password Reset Pages

**Mobile (320px):**
```
1. Visit /account/password-reset/ on mobile
2. Verify form is full-width and readable
3. Verify button is large enough to tap
4. Verify steps/content is visible without horizontal scroll
```

**Tablet (768px):**
```
1. Visit password reset pages on tablet/iPad
2. Verify 2-column layout displays correctly
3. Verify all content is readable
4. Verify spacing is appropriate
```

**Desktop (1024px+):**
```
1. Full 2-column layout should show
2. Left side shows step-by-step guide
3. Right side shows form
4. All spacing and typography correct
```

---

## Email Template Testing

### Test All Email Types

**Welcome Email:**
- Register new user
- Verify features list displays
- Verify dashboard link works
- Check responsiveness on mobile/desktop

**Password Reset Email:**
- Verify reset link is correct
- Check 24-hour expiration notice
- Verify security tips display
- Test link clicking

**Contact Form Email:**
- Submit contact form
- Verify admin gets email
- Check sender details are complete
- Verify reply-to email is set

**Newsletter Email:**
- Send from admin interface
- Check featured items display
- Verify "Shop Now" button works
- Check unsubscribe/preferences link

---

## Security Verification

### CSRF Protection
```
1. Inspect form HTML on any form page
2. Verify {% csrf_token %} is present
3. Attempt form submission without token
4. Should get CSRF validation error
```

### Secure Cookies (Production)
```javascript
// In browser DevTools console on production (HTTPS)
console.log(document.cookie);
// Should show: sessionid=xxx; Path=/; Secure; HttpOnly; SameSite=Lax
```

### Password Reset Security
```
1. Start password reset flow
2. Verify email contains unique token
3. Wait 24+ hours (or manually expire)
4. Attempt using expired link
5. Should show "Invalid or Expired Link" message
```

---

## Troubleshooting

### Email Not Sending

**Development (Console Backend):**
- Check Django console output for email content
- Verify DEBUG=True in settings
- Check settings.py has EMAIL_BACKEND set correctly

**Production (SMTP):**
- Verify EMAIL_HOST_USER and EMAIL_HOST_PASSWORD are set
- Check Gmail allows "Less secure app access" or use App Password
- Verify SMTP credentials by testing in Python:
```python
import smtplib
server = smtplib.SMTP('smtp.gmail.com', 587)
server.starttls()
server.login('your_email@gmail.com', 'your_app_password')
server.quit()
```

### SMS Not Sending

- Verify TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN are correct
- Check SMS_ENABLED=True
- Verify Twilio has credits/active account
- Check phone number format (must include country code)
- Test with Twilio's test account SID first

### Admin Panel Not Showing Communications

- Ensure accounts/admin.py is properly loaded
- Run: `python manage.py shell` then `from accounts.admin import *`
- Check for import errors in Django console

---

## Performance Optimization

### Large Newsletter Sends

For sending to 1000+ users:
```python
# Good approach - batches
from accounts.email_utils import send_batch_newsletter
users = User.objects.all()
success, total = send_batch_newsletter(list(users))

# Consider using Celery for async:
# from accounts.tasks import send_newsletter_task
# send_newsletter_task.delay(user_id)
```

---

## Next Steps

### Phase 3 (Future):

1. **Order Management System**
   - Create Order model if not exists
   - Wire order signals for email/SMS
   - Add order status tracking

2. **Advanced Features**
   - SMS delivery tracking
   - Email bounce handling
   - User preference center
   - Unsubscribe handling
   - Two-factor authentication via SMS

3. **Analytics**
   - Email open rates
   - Click tracking
   - SMS delivery rates
   - User engagement metrics

---

## Important URLs

- **Password Reset:** /account/password-reset/
- **Contact Form:** /contact/
- **Register:** /account/register/
- **Login:** /account/login/
- **Admin Panel:** /admin/
- **Email Templates:** accounts/templates/emails/
- **Email Utilities:** accounts/email_utils.py
- **SMS Utilities:** accounts/sms_utils.py
- **Settings:** teebusiness_core/settings.py

---

## File Reference

| File | Purpose | Modified |
|------|---------|----------|
| accounts/email_utils.py | Email sending module | NEW |
| accounts/sms_utils.py | SMS sending module | NEW |
| accounts/admin.py | Admin communications interface | MODIFIED |
| accounts/views.py | Email integration with views | MODIFIED |
| accounts/urls.py | Custom password reset views | MODIFIED |
| pages/views.py | Contact form email sending | MODIFIED |
| teebusiness_core/constants.py | Contact info constants | NEW |
| teebusiness_core/settings.py | Email/SMS/Security config | MODIFIED |
| templates/base.html | Footer restructure | MODIFIED |
| accounts/templates/accounts/password_reset.html | Premium redesign | MODIFIED |
| accounts/templates/accounts/password_reset_confirm.html | Premium redesign | MODIFIED |
| accounts/templates/accounts/password_reset_done.html | Premium redesign | MODIFIED |
| accounts/templates/accounts/password_reset_complete.html | Premium redesign | MODIFIED |
| accounts/templates/emails/*.html | 6 email templates | NEW |

---

**Setup Time:** ~15 minutes
**Testing Time:** ~30-45 minutes  
**Total:** ~1 hour

Good luck! 🚀
