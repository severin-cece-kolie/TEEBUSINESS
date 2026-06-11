from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
import uuid

User = get_user_model()


class NewsletterSubscriber(models.Model):
    """Model for managing newsletter subscribers."""
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('unsubscribed', 'Unsubscribed'),
        ('pending', 'Pending Verification'),
        ('bounced', 'Bounced'),
    ]
    
    SOURCE_CHOICES = [
        ('website', 'Website'),
        ('checkout', 'Checkout'),
        ('admin', 'Admin'),
        ('import', 'Import'),
        ('social', 'Social Media'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    full_name = models.CharField(max_length=255, blank=True)
    # Nullable + unique: lets phone-only subscribers exist (SQLite/Postgres treat
    # multiple NULLs as distinct, so uniqueness still holds for real emails).
    email = models.EmailField(unique=True, null=True, blank=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    subscription_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='website')
    verification_token = models.CharField(max_length=100, blank=True, null=True)
    verified_at = models.DateTimeField(blank=True, null=True)
    unsubscribed_at = models.DateTimeField(blank=True, null=True)
    unsubscribe_reason = models.TextField(blank=True, null=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-subscription_date']
        verbose_name = 'Newsletter Subscriber'
        verbose_name_plural = 'Newsletter Subscribers'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['status']),
            models.Index(fields=['subscription_date']),
        ]
    
    def __str__(self):
        return f"{self.full_name} ({self.email})"
    
    def activate(self):
        """Activate the subscriber."""
        self.status = 'active'
        self.verified_at = timezone.now()
        self.verification_token = None
        self.save()
    
    def unsubscribe(self, reason=''):
        """Unsubscribe the subscriber."""
        self.status = 'unsubscribed'
        self.unsubscribed_at = timezone.now()
        self.unsubscribe_reason = reason
        self.save()


class EmailCampaign(models.Model):
    """Model for managing email campaigns."""
    
    CAMPAIGN_TYPE_CHOICES = [
        ('promotional', 'Promotional'),
        ('restock', 'Restock Alert'),
        ('new_arrival', 'New Arrival'),
        ('discount', 'Discount Campaign'),
        ('announcement', 'Announcement'),
        ('newsletter', 'Newsletter'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('sending', 'Sending'),
        ('sent', 'Sent'),
        ('paused', 'Paused'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    campaign_type = models.CharField(max_length=20, choices=CAMPAIGN_TYPE_CHOICES)
    subject = models.CharField(max_length=255)
    preview_text = models.CharField(max_length=255, blank=True, help_text="Text shown in email preview")
    html_content = models.TextField()
    plain_text_content = models.TextField(blank=True)
    from_email = models.EmailField(default=settings.DEFAULT_FROM_EMAIL)
    reply_to = models.EmailField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    target_subscribers = models.ManyToManyField(
        NewsletterSubscriber,
        through='CampaignRecipient',
        related_name='campaigns'
    )
    total_recipients = models.PositiveIntegerField(default=0)
    sent_count = models.PositiveIntegerField(default=0)
    delivered_count = models.PositiveIntegerField(default=0)
    opened_count = models.PositiveIntegerField(default=0)
    clicked_count = models.PositiveIntegerField(default=0)
    failed_count = models.PositiveIntegerField(default=0)
    scheduled_for = models.DateTimeField(blank=True, null=True)
    sent_at = models.DateTimeField(blank=True, null=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_campaigns'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Email Campaign'
        verbose_name_plural = 'Email Campaigns'
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['campaign_type']),
            models.Index(fields=['scheduled_for']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.campaign_type})"
    
    def get_progress_percentage(self):
        """Calculate campaign progress percentage."""
        if self.total_recipients == 0:
            return 0
        return (self.sent_count / self.total_recipients) * 100
    
    def get_open_rate(self):
        """Calculate email open rate."""
        if self.sent_count == 0:
            return 0
        return (self.opened_count / self.sent_count) * 100
    
    def get_click_rate(self):
        """Calculate email click rate."""
        if self.sent_count == 0:
            return 0
        return (self.clicked_count / self.sent_count) * 100


class CampaignRecipient(models.Model):
    """Through model for campaign-subscriber relationship with tracking."""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('opened', 'Opened'),
        ('clicked', 'Clicked'),
        ('failed', 'Failed'),
        ('bounced', 'Bounced'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    campaign = models.ForeignKey(EmailCampaign, on_delete=models.CASCADE)
    subscriber = models.ForeignKey(NewsletterSubscriber, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    sent_at = models.DateTimeField(blank=True, null=True)
    delivered_at = models.DateTimeField(blank=True, null=True)
    opened_at = models.DateTimeField(blank=True, null=True)
    clicked_at = models.DateTimeField(blank=True, null=True)
    failed_at = models.DateTimeField(blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)
    tracking_id = models.CharField(max_length=100, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['campaign', 'subscriber']
        ordering = ['-created_at']
        verbose_name = 'Campaign Recipient'
        verbose_name_plural = 'Campaign Recipients'
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['tracking_id']),
        ]
    
    def __str__(self):
        return f"{self.subscriber.email} - {self.campaign.name}"
    
    def save(self, *args, **kwargs):
        if not self.tracking_id:
            self.tracking_id = str(uuid.uuid4())
        super().save(*args, **kwargs)


class EmailHistory(models.Model):
    """Model for tracking all sent emails."""
    
    EMAIL_TYPE_CHOICES = [
        ('otp', 'OTP Verification'),
        ('welcome', 'Welcome Email'),
        ('password_reset', 'Password Reset'),
        ('campaign', 'Campaign Email'),
        ('notification', 'Notification'),
        ('transactional', 'Transactional'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
        ('bounced', 'Bounced'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email_type = models.CharField(max_length=20, choices=EMAIL_TYPE_CHOICES)
    to_email = models.EmailField()
    from_email = models.EmailField()
    subject = models.CharField(max_length=255)
    body = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True, null=True)
    campaign = models.ForeignKey(
        EmailCampaign,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='email_history'
    )
    related_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sent_emails'
    )
    sent_at = models.DateTimeField(blank=True, null=True)
    delivered_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Email History'
        verbose_name_plural = 'Email History'
        indexes = [
            models.Index(fields=['to_email']),
            models.Index(fields=['email_type']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.subject} to {self.to_email}"
