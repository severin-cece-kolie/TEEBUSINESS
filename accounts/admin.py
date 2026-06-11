from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.urls import path, reverse
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from django.utils.html import format_html
from django.http import HttpResponse
import csv

from .models import User, OTP, LoginSecurityLog
from .email_utils import send_batch_newsletter
from .sms_utils import send_batch_promotional_sms


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'is_email_verified', 'is_active', 'is_staff',
                    'failed_login_attempts', 'is_locked_display', 'created_at']
    list_filter = ['is_active', 'is_staff', 'is_superuser', 'is_email_verified', 'created_at']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'phone_number']
    readonly_fields = ['id', 'last_login', 'date_joined', 'created_at', 'updated_at',
                       'last_login_ip', 'last_failed_login_ip', 'last_failed_login_at',
                       'email_verification_date']
    actions = ['unlock_accounts', 'reset_failed_attempts', 'verify_emails', 'send_otp_email_action']

    fieldsets = (
        ('Authentication', {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'email', 'phone_number')}),
        ('Email Verification', {'fields': ('is_email_verified', 'email_verification_date',
                                           'requires_email_verification')}),
        ('Security', {'fields': ('is_active', 'is_staff', 'is_superuser',
                                 'groups', 'user_permissions')}),
        ('Login Security', {'fields': ('failed_login_attempts', 'locked_until',
                                       'last_login_ip', 'last_failed_login_ip',
                                       'last_failed_login_at')}),
        ('Important Dates', {'fields': ('last_login', 'date_joined', 'created_at', 'updated_at')}),
        ('Metadata', {'fields': ('id',), 'classes': ('collapse',)}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2'),
        }),
    )

    def is_locked_display(self, obj):
        if obj.is_locked():
            return format_html('<span style="color:red;font-weight:bold;">Locked</span>')
        return format_html('<span style="color:green;">Active</span>')
    is_locked_display.short_description = 'Lock Status'
    is_locked_display.admin_order_field = 'locked_until'

    def unlock_accounts(self, request, queryset):
        count = 0
        for user in queryset:
            if user.is_locked():
                user.unlock_account()
                count += 1
        messages.success(request, f'{count} account(s) unlocked.')
    unlock_accounts.short_description = 'Unlock selected accounts'

    def reset_failed_attempts(self, request, queryset):
        count = queryset.update(failed_login_attempts=0, locked_until=None)
        messages.success(request, f'{count} user(s) had failed attempts reset.')
    reset_failed_attempts.short_description = 'Reset failed login attempts'

    def verify_emails(self, request, queryset):
        count = queryset.update(is_email_verified=True,
                                email_verification_date=timezone.now())
        messages.success(request, f'{count} email(s) verified.')
    verify_emails.short_description = 'Mark emails as verified'

    def send_otp_email_action(self, request, queryset):
        from .utils import generate_otp, send_otp_email
        count = 0
        for user in queryset.filter(is_email_verified=False):
            otp = generate_otp(user, purpose='email_verification')
            send_otp_email(user, otp)
            count += 1
        messages.success(request, f'OTP sent to {count} user(s).')
    send_otp_email_action.short_description = 'Send OTP verification email'


@admin.register(OTP)
class OTPAdmin(admin.ModelAdmin):
    list_display = ['user', 'code', 'purpose', 'is_used', 'expires_at', 'created_at']
    list_filter = ['purpose', 'is_used', 'created_at', 'expires_at']
    search_fields = ['user__username', 'user__email', 'code']
    readonly_fields = ['id', 'created_at', 'used_at']
    actions = ['invalidate_otps', 'delete_expired_otps']

    fieldsets = (
        ('OTP Information', {'fields': ('user', 'code', 'purpose')}),
        ('Status', {'fields': ('is_used', 'used_at', 'expires_at')}),
        ('Metadata', {'fields': ('ip_address', 'id', 'created_at'), 'classes': ('collapse',)}),
    )

    def invalidate_otps(self, request, queryset):
        count = queryset.filter(is_used=False).update(is_used=True, used_at=timezone.now())
        messages.success(request, f'{count} OTP(s) invalidated.')
    invalidate_otps.short_description = 'Invalidate selected OTPs'

    def delete_expired_otps(self, request, queryset):
        count = queryset.filter(expires_at__lt=timezone.now()).delete()[0]
        messages.success(request, f'{count} expired OTP(s) deleted.')
    delete_expired_otps.short_description = 'Delete expired OTPs'


@admin.register(LoginSecurityLog)
class LoginSecurityLogAdmin(admin.ModelAdmin):
    list_display = ['event_type', 'user', 'username_attempted', 'ip_address', 'created_at']
    list_filter = ['event_type', 'created_at']
    search_fields = ['user__username', 'username_attempted', 'ip_address']
    readonly_fields = ['id', 'created_at']

    fieldsets = (
        ('Event Information', {'fields': ('event_type', 'user', 'username_attempted')}),
        ('Request Information', {'fields': ('ip_address', 'user_agent')}),
        ('Details', {'fields': ('details',)}),
        ('Metadata', {'fields': ('id', 'created_at'), 'classes': ('collapse',)}),
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


# ─────────────────────────────────────────────────────────────
# Communications Admin Center
# ─────────────────────────────────────────────────────────────

class CommunicationsAdminView:
    """Custom admin dashboard for mass communications."""

    def __init__(self, admin_site):
        self.admin_site = admin_site

    def get_urls(self):
        site = self.admin_site
        wrap = site.admin_view   # ensures staff-only access + CSRF
        return [
            path('communications/',
                 wrap(self.communications_index),
                 name='communications_index'),
            path('communications/newsletter/',
                 wrap(self.send_newsletter_view),
                 name='send_newsletter'),
            path('communications/promo-email/',
                 wrap(self.send_promo_email_view),
                 name='send_promo_email'),
            path('communications/promo-sms/',
                 wrap(self.send_promo_sms_view),
                 name='send_promo_sms'),
            path('communications/history/',
                 wrap(self.message_history_view),
                 name='message_history'),
        ]

    # ── helpers ──────────────────────────────────────────────

    def _ctx(self, request, **extra):
        """Merge admin site context with extra keys."""
        ctx = self.admin_site.each_context(request)
        ctx.update(extra)
        return ctx

    # ── views ────────────────────────────────────────────────

    def communications_index(self, request):
        actions = [
            {
                'name': 'Send Newsletter',
                'description': 'Send a newsletter to all registered users',
                'url': reverse('admin:send_newsletter'),
                'color': '#3b82f6',
            },
            {
                'name': 'Send Promotional Email',
                'description': 'Send a custom promotional email to selected users',
                'url': reverse('admin:send_promo_email'),
                'color': '#8b5cf6',
            },
            {
                'name': 'Send Promotional SMS',
                'description': 'Send a promotional SMS to users with phone numbers',
                'url': reverse('admin:send_promo_sms'),
                'color': '#10b981',
            },
            {
                'name': 'Message History',
                'description': 'View all sent messages and delivery status',
                'url': reverse('admin:message_history'),
                'color': '#f59e0b',
            },
        ]
        ctx = self._ctx(request, title='Communications Center', actions=actions)
        return render(request, 'admin/communications_dashboard.html', ctx)

    def send_newsletter_view(self, request):
        if request.method == 'POST':
            user_ids = request.POST.getlist('users')
            select_all = request.POST.get('select_all') == '1'

            if select_all:
                users = list(User.objects.filter(is_active=True, is_email_verified=True))
            elif user_ids:
                users = list(User.objects.filter(id__in=user_ids,
                                                  is_active=True, is_email_verified=True))
            else:
                messages.error(request, 'Please select at least one recipient.')
                users = None

            if users:
                success, total = send_batch_newsletter(users, request=request)
                level = messages.SUCCESS if success == total else messages.WARNING
                messages.add_message(request, level,
                                     f'Newsletter sent: {success}/{total} delivered.')
                return redirect(reverse('admin:communications_index'))

        users = User.objects.filter(is_active=True, is_email_verified=True).order_by('-date_joined')
        ctx = self._ctx(request, title='Send Newsletter', users=users, action='newsletter')
        return render(request, 'admin/communications_form.html', ctx)

    def send_promo_email_view(self, request):
        from django.core.mail import EmailMultiAlternatives
        from django.conf import settings as dj_settings

        if request.method == 'POST':
            user_ids = request.POST.getlist('users')
            select_all = request.POST.get('select_all') == '1'
            subject = request.POST.get('subject', '').strip()
            message_html = request.POST.get('message', '').strip()

            if not subject or not message_html:
                messages.error(request, 'Subject and message body are required.')
            else:
                if select_all:
                    recipients = User.objects.filter(is_active=True, is_email_verified=True)
                elif user_ids:
                    recipients = User.objects.filter(id__in=user_ids,
                                                      is_active=True, is_email_verified=True)
                else:
                    messages.error(request, 'Please select at least one recipient.')
                    recipients = User.objects.none()

                success = 0
                failed = 0
                for user in recipients:
                    try:
                        msg = EmailMultiAlternatives(
                            subject=subject,
                            body='',
                            from_email=dj_settings.DEFAULT_FROM_EMAIL,
                            to=[user.email],
                        )
                        msg.attach_alternative(message_html, 'text/html')
                        msg.send()
                        success += 1
                    except Exception:
                        failed += 1

                level = messages.SUCCESS if failed == 0 else messages.WARNING
                messages.add_message(request, level,
                                     f'Promotional email sent: {success} delivered, {failed} failed.')
                return redirect(reverse('admin:communications_index'))

        users = User.objects.filter(is_active=True, is_email_verified=True).order_by('-date_joined')
        ctx = self._ctx(request, title='Send Promotional Email', users=users, action='email')
        return render(request, 'admin/communications_form.html', ctx)

    def send_promo_sms_view(self, request):
        if request.method == 'POST':
            user_ids = request.POST.getlist('users')
            select_all = request.POST.get('select_all') == '1'
            message_text = request.POST.get('message', '').strip()

            if not message_text:
                messages.error(request, 'Message is required.')
            elif len(message_text) > 160:
                messages.error(request, 'SMS message must be 160 characters or fewer.')
            else:
                if select_all:
                    phone_numbers = list(
                        User.objects.filter(is_active=True)
                        .exclude(phone_number__isnull=True)
                        .exclude(phone_number='')
                        .values_list('phone_number', flat=True)
                    )
                elif user_ids:
                    phone_numbers = list(
                        User.objects.filter(id__in=user_ids)
                        .exclude(phone_number__isnull=True)
                        .exclude(phone_number='')
                        .values_list('phone_number', flat=True)
                    )
                else:
                    messages.error(request, 'Please select at least one recipient.')
                    phone_numbers = []

                if phone_numbers:
                    success, total = send_batch_promotional_sms(phone_numbers, message_text)
                    messages.success(request,
                                     f'SMS sent: {success}/{total} delivered.')
                    return redirect(reverse('admin:communications_index'))

        users = (User.objects.filter(is_active=True)
                 .exclude(phone_number__isnull=True)
                 .exclude(phone_number='')
                 .order_by('-date_joined'))
        ctx = self._ctx(request, title='Send Promotional SMS',
                        users=users, action='sms', char_limit=160)
        return render(request, 'admin/communications_form.html', ctx)

    def message_history_view(self, request):
        from communication.models import EmailHistory
        history = (EmailHistory.objects
                   .select_related('related_user', 'campaign')
                   .order_by('-created_at')[:100])
        ctx = self._ctx(request, title='Message History', history=history)
        return render(request, 'admin/message_history.html', ctx)


# ─────────────────────────────────────────────────────────────
# Register communication URLs with the admin site.
# We patch AdminSite.get_urls once at import time so that
# these URLs appear in the admin: namespace.
# ─────────────────────────────────────────────────────────────

_original_admin_get_urls = admin.AdminSite.get_urls


def _admin_get_urls_with_comms(self):
    comm = CommunicationsAdminView(self)
    return comm.get_urls() + _original_admin_get_urls(self)


admin.AdminSite.get_urls = _admin_get_urls_with_comms
