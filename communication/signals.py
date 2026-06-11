"""
Automatic product alerts.

Subscribers are notified when a product is:
  * newly added           → 'new_arrival'   (Product created)
  * discounted            → 'discount'      (discount_percent 0 → >0)
  * restocked             → 'restock'       (a size's quantity 0 → >0)

Detection compares the incoming instance against the stored row in pre_save,
then fires after the row commits (transaction.on_commit) so emails reflect
data that actually persisted. `raw=True` saves (fixtures/loaddata) are ignored.
"""

from django.conf import settings
from django.db import transaction
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from shop.models import Product, ProductSize

from .tasks import send_product_notification_task


def _notifications_enabled():
    return getattr(settings, 'PRODUCT_NOTIFICATIONS_ENABLED', True)


@receiver(pre_save, sender=Product)
def product_pre_save(sender, instance, raw=False, **kwargs):
    if raw or not instance.pk:
        instance._discount_started = False
        return
    old = Product.objects.filter(pk=instance.pk).only('discount_percent').first()
    instance._discount_started = bool(
        old and (old.discount_percent or 0) == 0 and (instance.discount_percent or 0) > 0
    )


@receiver(post_save, sender=Product)
def product_post_save(sender, instance, created, raw=False, **kwargs):
    if raw or not _notifications_enabled():
        return
    if created:
        transaction.on_commit(
            lambda: send_product_notification_task(instance.id, 'new_arrival')
        )
    elif getattr(instance, '_discount_started', False):
        transaction.on_commit(
            lambda: send_product_notification_task(instance.id, 'discount')
        )


@receiver(pre_save, sender=ProductSize)
def size_pre_save(sender, instance, raw=False, **kwargs):
    if raw or not instance.pk:
        instance._restocked = False
        return
    old = ProductSize.objects.filter(pk=instance.pk).only('quantity').first()
    instance._restocked = bool(old and old.quantity == 0 and instance.quantity > 0)


@receiver(post_save, sender=ProductSize)
def size_post_save(sender, instance, created, raw=False, **kwargs):
    if raw or created or not _notifications_enabled():
        return
    if getattr(instance, '_restocked', False):
        transaction.on_commit(
            lambda: send_product_notification_task(instance.product_id, 'restock')
        )
