from django.contrib import admin
from django.contrib import messages
from django.utils.html import format_html
from django.urls import reverse
from django.http import HttpResponse
import csv

from unfold.admin import ModelAdmin, TabularInline
from import_export.admin import ImportExportModelAdmin
from import_export import resources
from import_export.formats import base_formats

from .models import NewsletterSubscriber, EmailCampaign, CampaignRecipient, EmailHistory

EXPORT_FORMATS = [base_formats.CSV, base_formats.XLSX, base_formats.JSON]


class SubscriberResource(resources.ModelResource):
    class Meta:
        model = NewsletterSubscriber
        fields = ('full_name', 'email', 'phone_number', 'status', 'source', 'subscription_date')
        export_order = fields


@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(ImportExportModelAdmin, ModelAdmin):
    """Admin interface for NewsletterSubscriber model."""

    resource_class = SubscriberResource
    formats = EXPORT_FORMATS
    list_display = ['full_name', 'email', 'status', 'source', 'subscription_date', 'verified_at']
    list_filter = ['status', 'source', 'subscription_date']
    search_fields = ['full_name', 'email', 'phone_number']
    readonly_fields = ['id', 'subscription_date', 'verified_at', 'unsubscribed_at', 'created_at', 'updated_at']
    actions = ['activate_subscribers', 'send_test_email', 'export_subscribers']
    
    fieldsets = (
        ('Subscriber Information', {
            'fields': ('full_name', 'email', 'phone_number')
        }),
        ('Subscription Status', {
            'fields': ('status', 'source', 'subscription_date', 'verified_at')
        }),
        ('Verification', {
            'fields': ('verification_token',),
            'classes': ('collapse',)
        }),
        ('Unsubscription', {
            'fields': ('unsubscribed_at', 'unsubscribe_reason'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('metadata', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def activate_subscribers(self, request, queryset):
        """Activate selected subscribers."""
        count = 0
        for subscriber in queryset.filter(status='pending'):
            subscriber.activate()
            count += 1
        messages.success(request, f'{count} subscribers activated successfully.')
    activate_subscribers.short_description = 'Activate selected subscribers'
    
    def send_test_email(self, request, queryset):
        """Send test email to selected subscribers."""
        from django.core.mail import send_mail
        from django.conf import settings
        
        count = 0
        for subscriber in queryset.filter(status='active')[:5]:  # Limit to 5 for testing
            try:
                send_mail(
                    subject='Test Email from TEEBUSINESS',
                    message='This is a test email.',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[subscriber.email],
                    fail_silently=False,
                )
                count += 1
            except Exception as e:
                messages.error(request, f'Failed to send to {subscriber.email}: {str(e)}')
        
        if count > 0:
            messages.success(request, f'Test email sent to {count} subscribers.')
    send_test_email.short_description = 'Send test email (max 5)'
    
    def export_subscribers(self, request, queryset):
        """Export selected subscribers to CSV."""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="subscribers.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Full Name', 'Email', 'Phone', 'Status', 'Source', 'Subscription Date'])
        
        for subscriber in queryset:
            writer.writerow([
                subscriber.full_name,
                subscriber.email,
                subscriber.phone_number or '',
                subscriber.status,
                subscriber.source,
                subscriber.subscription_date.strftime('%Y-%m-%d %H:%M:%S')
            ])
        
        return response
    export_subscribers.short_description = 'Export selected to CSV'


class CampaignRecipientInline(TabularInline):
    """Inline admin for campaign recipients."""
    model = CampaignRecipient
    extra = 0
    readonly_fields = ['subscriber', 'status', 'sent_at', 'delivered_at', 'opened_at']
    can_delete = False


@admin.register(EmailCampaign)
class EmailCampaignAdmin(ModelAdmin):
    """Admin interface for EmailCampaign model."""
    
    list_display = ['name', 'campaign_type', 'status', 'total_recipients', 'sent_count', 'get_progress_percentage', 'scheduled_for', 'created_at']
    list_filter = ['status', 'campaign_type', 'created_at', 'scheduled_for']
    search_fields = ['name', 'subject']
    readonly_fields = ['id', 'sent_count', 'delivered_count', 'opened_count', 'clicked_count', 'failed_count', 'sent_at', 'created_at', 'updated_at']
    inlines = [CampaignRecipientInline]
    actions = ['send_campaign', 'duplicate_campaign', 'cancel_campaign']
    
    fieldsets = (
        ('Campaign Information', {
            'fields': ('name', 'campaign_type', 'status')
        }),
        ('Email Content', {
            'fields': ('subject', 'preview_text', 'html_content', 'plain_text_content')
        }),
        ('Email Settings', {
            'fields': ('from_email', 'reply_to')
        }),
        ('Recipients', {
            'fields': ()  # Managed through CampaignRecipient inline
        }),
        ('Statistics', {
            'fields': ('total_recipients', 'sent_count', 'delivered_count', 'opened_count', 'clicked_count', 'failed_count'),
            'classes': ('collapse',)
        }),
        ('Scheduling', {
            'fields': ('scheduled_for', 'sent_at')
        }),
        ('Metadata', {
            'fields': ('id', 'created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_progress_percentage(self, obj):
        """Display progress as a progress bar."""
        percentage = obj.get_progress_percentage()
        return format_html(
            '<progress value="{0}" max="100"></progress> {0:.1f}%',
            percentage
        )
    get_progress_percentage.short_description = 'Progress'
    
    def send_campaign(self, request, queryset):
        """Send selected draft campaigns to all active newsletter subscribers."""
        from django.core.mail import EmailMultiAlternatives
        from django.utils import timezone as tz

        sent_campaigns = 0

        for campaign in queryset.filter(status='draft'):
            subscribers = NewsletterSubscriber.objects.filter(status='active')
            total = subscribers.count()

            if total == 0:
                messages.warning(request,
                                  f'Campaign "{campaign.name}": no active subscribers found.')
                continue

            campaign.total_recipients = total
            campaign.status = 'sending'
            campaign.save(update_fields=['total_recipients', 'status'])

            sent = failed = 0

            for subscriber in subscribers:
                recipient, _ = CampaignRecipient.objects.get_or_create(
                    campaign=campaign,
                    subscriber=subscriber,
                )
                try:
                    msg = EmailMultiAlternatives(
                        subject=campaign.subject,
                        body=(campaign.plain_text_content
                              or 'Please view this email in an HTML-compatible client.'),
                        from_email=campaign.sender_email,
                        to=[subscriber.email],
                        reply_to=[campaign.reply_to] if campaign.reply_to else None,
                    )
                    msg.attach_alternative(campaign.html_content, 'text/html')
                    msg.send()

                    recipient.status = 'sent'
                    recipient.sent_at = tz.now()
                    recipient.save(update_fields=['status', 'sent_at'])
                    sent += 1
                except Exception as exc:
                    recipient.status = 'failed'
                    recipient.error_message = str(exc)
                    recipient.failed_at = tz.now()
                    recipient.save(update_fields=['status', 'error_message', 'failed_at'])
                    failed += 1

            campaign.sent_count = sent
            campaign.failed_count = failed
            campaign.status = 'sent'
            campaign.sent_at = tz.now()
            campaign.save(update_fields=['sent_count', 'failed_count', 'status', 'sent_at'])

            sent_campaigns += 1
            messages.success(
                request,
                f'Campaign "{campaign.name}" sent: {sent} delivered, {failed} failed.',
            )

        if sent_campaigns == 0 and not queryset.filter(status='draft').exists():
            messages.warning(request, 'Only draft campaigns can be sent.')
    send_campaign.short_description = 'Send selected draft campaigns'
    
    def duplicate_campaign(self, request, queryset):
        """Duplicate selected campaigns."""
        count = 0
        for campaign in queryset:
            new_campaign = EmailCampaign.objects.create(
                name=f'{campaign.name} (Copy)',
                campaign_type=campaign.campaign_type,
                subject=campaign.subject,
                preview_text=campaign.preview_text,
                html_content=campaign.html_content,
                plain_text_content=campaign.plain_text_content,
                from_email=campaign.from_email,
                reply_to=campaign.reply_to,
                status='draft',
                created_by=request.user
            )
            count += 1
        
        messages.success(request, f'{count} campaigns duplicated successfully.')
    duplicate_campaign.short_description = 'Duplicate selected campaigns'
    
    def cancel_campaign(self, request, queryset):
        """Cancel selected campaigns."""
        count = queryset.filter(status__in=['scheduled', 'sending']).update(status='cancelled')
        messages.success(request, f'{count} campaigns cancelled.')
    cancel_campaign.short_description = 'Cancel selected campaigns'
    
    def save_model(self, request, obj, form, change):
        """Set created_by on new campaigns."""
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(CampaignRecipient)
class CampaignRecipientAdmin(ModelAdmin):
    """Admin interface for CampaignRecipient model."""
    
    list_display = ['subscriber', 'campaign', 'status', 'sent_at', 'delivered_at', 'opened_at']
    list_filter = ['status', 'sent_at', 'delivered_at']
    search_fields = ['subscriber__email', 'campaign__name', 'tracking_id']
    readonly_fields = ['id', 'tracking_id', 'sent_at', 'delivered_at', 'opened_at', 'clicked_at', 'failed_at', 'created_at']
    
    fieldsets = (
        ('Recipient Information', {
            'fields': ('campaign', 'subscriber')
        }),
        ('Status', {
            'fields': ('status', 'sent_at', 'delivered_at', 'opened_at', 'clicked_at', 'failed_at')
        }),
        ('Error Information', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        }),
        ('Tracking', {
            'fields': ('tracking_id', 'created_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(EmailHistory)
class EmailHistoryAdmin(ModelAdmin):
    """Admin interface for EmailHistory model."""
    
    list_display = ['subject', 'to_email', 'email_type', 'status', 'sent_at', 'created_at']
    list_filter = ['email_type', 'status', 'created_at']
    search_fields = ['subject', 'to_email', 'from_email']
    readonly_fields = ['id', 'sent_at', 'delivered_at', 'created_at']
    
    fieldsets = (
        ('Email Information', {
            'fields': ('email_type', 'to_email', 'from_email', 'subject')
        }),
        ('Content', {
            'fields': ('body',)
        }),
        ('Status', {
            'fields': ('status', 'sent_at', 'delivered_at')
        }),
        ('Related Objects', {
            'fields': ('campaign', 'related_user')
        }),
        ('Error Information', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('id', 'created_at'),
            'classes': ('collapse',)
        }),
    )
