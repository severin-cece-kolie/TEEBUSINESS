from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils import timezone
import uuid


class CustomUserManager(BaseUserManager):
    """Custom user manager for email-based authentication."""
    
    def create_user(self, username, email, password=None, **extra_fields):
        """Create and save a regular user."""
        if not email:
            raise ValueError('The Email field must be set')
        if not username:
            raise ValueError('The Username field must be set')
        
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, username, email, password=None, **extra_fields):
        """Create and save a superuser."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(username, email, password, **extra_fields)


class User(AbstractUser):
    """Custom User model with OTP verification support."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    # Optional profile details — can be completed later from Profile Settings.
    address = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    is_email_verified = models.BooleanField(default=False)
    email_verification_date = models.DateTimeField(blank=True, null=True)
    failed_login_attempts = models.PositiveIntegerField(default=0)
    locked_until = models.DateTimeField(blank=True, null=True)
    last_login_ip = models.GenericIPAddressField(blank=True, null=True)
    last_failed_login_ip = models.GenericIPAddressField(blank=True, null=True)
    last_failed_login_at = models.DateTimeField(blank=True, null=True)
    requires_email_verification = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = CustomUserManager()
    
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['is_email_verified']),
            models.Index(fields=['locked_until']),
        ]
    
    def __str__(self):
        return f"{self.username} ({self.email})"
    
    def is_locked(self):
        """Check if account is locked due to failed attempts."""
        if self.locked_until and self.locked_until > timezone.now():
            return True
        return False
    
    def lock_account(self, duration_minutes=15):
        """Lock account for specified duration."""
        from datetime import timedelta
        self.locked_until = timezone.now() + timedelta(minutes=duration_minutes)
        self.save()
    
    def unlock_account(self):
        """Unlock account."""
        self.locked_until = None
        self.failed_login_attempts = 0
        self.save()
    
    def record_failed_login(self, ip_address):
        """Record a failed login attempt."""
        self.failed_login_attempts += 1
        self.last_failed_login_ip = ip_address
        self.last_failed_login_at = timezone.now()
        
        # Lock after 5 failed attempts
        if self.failed_login_attempts >= 5:
            self.lock_account(duration_minutes=15)
        
        # Require email verification after 10 failed attempts
        if self.failed_login_attempts >= 10:
            self.requires_email_verification = True
        
        self.save()
    
    def record_successful_login(self, ip_address):
        """Record a successful login and reset failed attempts."""
        self.failed_login_attempts = 0
        self.last_login_ip = ip_address
        self.last_failed_login_ip = None
        self.last_failed_login_at = None
        self.save()


class OTP(models.Model):
    """Model for storing OTP codes for email verification."""
    
    PURPOSE_CHOICES = [
        ('email_verification', 'Email Verification'),
        ('password_reset', 'Password Reset'),
        ('login_verification', 'Login Verification'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='otps')
    code = models.CharField(max_length=6)  # 6-digit OTP
    purpose = models.CharField(max_length=30, choices=PURPOSE_CHOICES)
    is_used = models.BooleanField(default=False)
    used_at = models.DateTimeField(blank=True, null=True)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'OTP'
        verbose_name_plural = 'OTPs'
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['user', 'purpose']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f"OTP for {self.user.username} ({self.purpose})"
    
    def is_valid(self):
        """Check if OTP is valid (not expired and not used)."""
        if self.is_used:
            return False
        if self.expires_at < timezone.now():
            return False
        return True
    
    def mark_as_used(self):
        """Mark OTP as used."""
        self.is_used = True
        self.used_at = timezone.now()
        self.save()


class LoginSecurityLog(models.Model):
    """Model for tracking login security events."""
    
    EVENT_TYPE_CHOICES = [
        ('login_success', 'Login Success'),
        ('login_failed', 'Login Failed'),
        ('logout', 'Logout'),
        ('account_locked', 'Account Locked'),
        ('account_unlocked', 'Account Unlocked'),
        ('password_changed', 'Password Changed'),
        ('otp_verified', 'OTP Verified'),
        ('otp_failed', 'OTP Failed'),
        ('suspicious_activity', 'Suspicious Activity'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='security_logs', blank=True, null=True)
    event_type = models.CharField(max_length=30, choices=EVENT_TYPE_CHOICES)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    username_attempted = models.CharField(max_length=150, blank=True, null=True)
    details = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Login Security Log'
        verbose_name_plural = 'Login Security Logs'
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['event_type']),
            models.Index(fields=['ip_address']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        user_info = self.user.username if self.user else self.username_attempted or 'Unknown'
        return f"{self.event_type} - {user_info} at {self.created_at}"
