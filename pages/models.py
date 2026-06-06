from django.db import models

class NewsletterSubscriber(models.Model):
    full_name = models.CharField(max_length=200, blank=True)
    email = models.EmailField(unique=True, blank=True, null=True)
    phone_number = models.CharField(max_length=50, unique=True, blank=True, null=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)
    source = models.CharField(max_length=100, default="Footer Form")

    class Meta:
        ordering = ['-subscribed_at']
        verbose_name = 'Newsletter Subscriber'
        verbose_name_plural = 'Newsletter Subscribers'

    def __str__(self):
        return self.email or self.phone_number or "Unknown Subscriber"
