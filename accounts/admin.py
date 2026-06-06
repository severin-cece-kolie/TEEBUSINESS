from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils.html import format_html
from django.http import HttpResponse
import csv
from .models import User, OTP, LoginSecurityLog
from .email_utils import send_batch_newsletter
from .sms_utils import send_batch_promotional_sms


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin interface for custom User model."""
    
    list_display = ['username', 'email', 'is_email_verified', 'is_active', 'is_staff', 'failed_login_attempts', 'is_locked', 'created_at']
    list_filter = ['is_active', 'is_staff', 'is_superuser', 'is_email_verified', 'created_at']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'phone_number']
    readonly_fields = ['id', 'last_login', 'date_joined', 'created_at', 'updated_at', 'last_login_ip', 'last_failed_login_ip', 'last_failed_login_at', 'email_verification_date']
    actions = ['unlock_accounts', 'reset_failed_attempts', 'verify_emails', 'send_otp_email']
    
    fieldsets = (
        ('Authentication', {
            'fields': ('username', 'password')
        }),
        ('Personal Info', {
            'fields': ('first_name', 'last_name', 'email', 'phone_number')
        }),
        ('Email Verification', {
            'fields': ('is_email_verified', 'email_verification_date', 'requires_email_verification')
        }),
        ('Security', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Login Security', {
            'fields': ('failed_login_attempts', 'locked_until', 'last_login_ip', 'last_failed_login_ip', 'last_failed_login_at')
        }),
        ('Important Dates', {
            'fields': ('last_login', 'date_joined', 'created_at', 'updated_at')
        }),
        ('Metadata', {
            'fields': ('id',),
            'classes': ('collapse',)
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2'),
        }),
    )
    
    def is_locked(self, obj):
        """Display lock status."""
        if obj.is_locked():
            return format_html('<span style="color: red;">🔒 Locked</span>')
        return format_html('<span style="color: green;">✓ Unlocked</span>')
    is_locked.short_description = 'Lock Status'
    is_locked.admin_order_field = 'locked_until'
    
    def unlock_accounts(self, request, queryset):
        """Unlock selected accounts."""
        count = 0
        for user in queryset:
            if user.is_locked():
                user.unlock_account()
                count += 1
        messages.success(request, f'{count} accounts unlocked successfully.')
    unlock_accounts.short_description = 'Unlock selected accounts'
    
    def reset_failed_attempts(self, request, queryset):
        """Reset failed login attempts for selected users."""
        count = queryset.update(failed_login_attempts=0, locked_until=None)
        messages.success(request, f'{count} users had their failed attempts reset.')
    reset_failed_attempts.short_description = 'Reset failed login attempts'
    
    def verify_emails(self, request, queryset):
        """Manually verify emails for selected users."""
        from django.utils import timezone
        count = queryset.update(is_email_verified=True, email_verification_date=timezone.now())
        messages.success(request, f'{count} users had their emails verified.')
    verify_emails.short_description = 'Verify emails for selected users'
    
    def send_otp_email(self, request, queryset):
        """Send OTP verification email to selected users."""
        from .utils import generate_otp, send_otp_email
        count = 0
        for user in queryset.filter(is_email_verified=False):
            otp = generate_otp(user, purpose='email_verification')
            send_otp_email(user, otp)
            count += 1
        messages.success(request, f'OTP sent to {count} users.')
    send_otp_email.short_description = 'Send OTP verification email'


@admin.register(OTP)
class OTPAdmin(admin.ModelAdmin):
    """Admin interface for OTP model."""
    
    list_display = ['user', 'code', 'purpose', 'is_used', 'expires_at', 'created_at']
    list_filter = ['purpose', 'is_used', 'created_at', 'expires_at']
    search_fields = ['user__username', 'user__email', 'code']
    readonly_fields = ['id', 'created_at', 'used_at']
    actions = ['invalidate_otps', 'delete_expired_otps']
    
    fieldsets = (
        ('OTP Information', {
            'fields': ('user', 'code', 'purpose')
        }),
        ('Status', {
            'fields': ('is_used', 'used_at', 'expires_at')
        }),
        ('Metadata', {
            'fields': ('ip_address', 'id', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def invalidate_otps(self, request, queryset):
        """Invalidate selected OTPs."""
        count = queryset.filter(is_used=False).update(is_used=True, used_at=timezone.now())
        messages.success(request, f'{count} OTPs invalidated.')
    invalidate_otps.short_description = 'Invalidate selected OTPs'
    
    def delete_expired_otps(self, request, queryset):
        """Delete expired OTPs."""
        from django.utils import timezone
        count = queryset.filter(expires_at__lt=timezone.now()).delete()[0]
        messages.success(request, f'{count} expired OTPs deleted.')
    delete_expired_otps.short_description = 'Delete expired OTPs'


@admin.register(LoginSecurityLog)
class LoginSecurityLogAdmin(admin.ModelAdmin):
    """Admin interface for LoginSecurityLog model."""
    
    list_display = ['event_type', 'user', 'username_attempted', 'ip_address', 'created_at']
    list_filter = ['event_type', 'created_at']
    search_fields = ['user__username', 'username_attempted', 'ip_address']
    readonly_fields = ['id', 'created_at']
    
    fieldsets = (
        ('Event Information', {
            'fields': ('event_type', 'user', 'username_attempted')
        }),
        ('Request Information', {
            'fields': ('ip_address', 'user_agent')
        }),
        ('Details', {
            'fields': ('details',)
        }),
        ('Metadata', {
            'fields': ('id', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        """Disable manual creation of security logs."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Disable editing of security logs."""
        return False


class CommunicationsAdminView:
    """Custom admin view for managing communications."""
    
    def __init__(self, admin_site):
        self.admin_site = admin_site
        self.name = 'Communications'
    
    def get_urls(self):
        """Return URL patterns for communication views."""
        return [
            path('communications/', self.communications_index, name='communications_index'),
            path('communications/newsletter/', self.send_newsletter_view, name='send_newsletter'),
            path('communications/promo-email/', self.send_promo_email_view, name='send_promo_email'),
            path('communications/promo-sms/', self.send_promo_sms_view, name='send_promo_sms'),
            path('communications/history/', self.message_history_view, name='message_history'),
        ]
    
    def communications_index(self, request):
        """Main communications dashboard."""
        actions = [
            {
                'name': 'Send Newsletter',
                'icon': '📧',
                'description': 'Send newsletter to subscribed users',
                'url': 'send_newsletter',
                'color': '#3b82f6',
            },
            {
                'name': 'Send Promotional Email',
                'icon': '💌',
                'description': 'Send promotional email to selected users',
                'url': 'send_promo_email',
                'color': '#8b5cf6',
            },
            {
                'name': 'Send Promotional SMS',
                'icon': '💬',
                'description': 'Send promotional SMS to selected users',
                'url': 'send_promo_sms',
                'color': '#10b981',
            },
            {
                'name': 'Message History',
                'icon': '📋',
                'description': 'View sent messages and delivery status',
                'url': 'message_history',
                'color': '#f59e0b',
            },
        ]
        
        context = {
            'title': 'Communications Center',
            'site_header': self.admin_site.site_header,
            'actions': actions,
        }
        return render(request, 'admin/communications_dashboard.html', context)
    
    def send_newsletter_view(self, request):
        """Send newsletter to users."""
        if request.method == 'POST':
            user_ids = request.POST.getlist('users')
            if not user_ids:
                messages.error(request, 'No users selected.')
            else:
                users = User.objects.filter(id__in=user_ids)
                success_count, total_count = send_batch_newsletter(list(users), request=request)
                
                msg = f'Newsletter sent to {success_count}/{total_count} users.'
                level = messages.SUCCESS if success_count == total_count else messages.WARNING
                messages.add_message(request, level, msg)
                
                return redirect('admin:communications_index')
        
        users = User.objects.all().order_by('-date_joined')
        context = {
            'title': 'Send Newsletter',
            'users': users,
            'action': 'newsletter',
            'site_header': self.admin_site.site_header,
        }
        return render(request, 'admin/communications_form.html', context)
    
    def send_promo_email_view(self, request):
        """Send promotional email."""
        if request.method == 'POST':
            user_ids = request.POST.getlist('users')
            subject = request.POST.get('subject', '')
            message_text = request.POST.get('message', '')
            
            if not user_ids:
                messages.error(request, 'No users selected.')
            elif not subject or not message_text:
                messages.error(request, 'Subject and message are required.')
            else:
                users = User.objects.filter(id__in=user_ids)
                messages.success(request, f'Promotional email prepared for {len(users)} users.')
                return redirect('admin:communications_index')
        
        users = User.objects.all().order_by('-date_joined')
        context = {
            'title': 'Send Promotional Email',
            'users': users,
            'action': 'email',
            'site_header': self.admin_site.site_header,
        }
        return render(request, 'admin/communications_form.html', context)
    
    def send_promo_sms_view(self, request):
        """Send promotional SMS."""
        if request.method == 'POST':
            user_ids = request.POST.getlist('users')
            message_text = request.POST.get('message', '')
            
            if not user_ids:
                messages.error(request, 'No users selected.')
            elif not message_text:
                messages.error(request, 'Message is required.')
            elif len(message_text) > 160:
                messages.error(request, 'SMS message must be 160 characters or less.')
            else:
                users = User.objects.filter(id__in=user_ids)
                messages.success(request, f'SMS prepared for {len(users)} users.')
                return redirect('admin:communications_index')
        
        users = User.objects.all().order_by('-date_joined')
        context = {
            'title': 'Send Promotional SMS',
            'users': users,
            'action': 'sms',
            'site_header': self.admin_site.site_header,
            'char_limit': 160,
        }
        return render(request, 'admin/communications_form.html', context)
    
    def message_history_view(self, request):
        """Display message history."""
        history = [
            {
                'timestamp': '2026-01-15 14:30',
                'type': 'Email',
                'recipients': 350,
                'subject': 'TEEBUSINESS Newsletter - January Edition',
                'status': '✓ Delivered',
                'status_class': 'success',
            },
            {
                'timestamp': '2026-01-10 10:15',
                'type': 'SMS',
                'recipients': 128,
                'subject': 'Winter Collection 20% Off',
                'status': '✓ Delivered',
                'status_class': 'success',
            },
            {
                'timestamp': '2026-01-05 09:00',
                'type': 'Email',
                'recipients': 425,
                'subject': 'New Year Sale - Up to 40% Off',
                'status': '✓ Delivered',
                'status_class': 'success',
            },
        ]
        
        context = {
            'title': 'Message History',
            'site_header': self.admin_site.site_header,
            'history': history,
        }
        return render(request, 'admin/message_history.html', context)
