"""
Auto-provision the full size run (EU 38–48) whenever a Product is created,
so the admin never has to add variants by hand. New sizes start at stock 0.
Idempotent and cheap (only runs on creation, bulk_create for missing sizes).
"""

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Product, ProductSize

DEFAULT_SIZES = [str(s) for s in range(38, 49)]  # 38, 39, … 48


@receiver(post_save, sender=Product)
def ensure_product_sizes(sender, instance, created, raw=False, **kwargs):
    if raw or not created:
        return
    existing = set(instance.sizes.values_list('size', flat=True))
    missing = [s for s in DEFAULT_SIZES if s not in existing]
    if missing:
        ProductSize.objects.bulk_create(
            [ProductSize(product=instance, size=s, quantity=0) for s in missing]
        )
