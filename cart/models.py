import uuid
from decimal import Decimal

from django.conf import settings
from django.db import models


class Order(models.Model):
    """A persisted customer order, created at checkout."""

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    PAYMENT_CHOICES = [
        ('mobile_money', 'Mobile Money'),
        ('card', 'Credit/Debit Card'),
        ('cod', 'Cash on Delivery'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order_number = models.CharField(max_length=20, unique=True, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='orders',
    )

    # Customer information
    full_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=30)
    email = models.EmailField()

    # Shipping address
    city = models.CharField(max_length=120)
    district = models.CharField(max_length=120, blank=True)
    address = models.TextField()

    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='cod')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # Money (GNF)
    subtotal_gnf = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    shipping_gnf = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_gnf = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_gnf = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['order_number']),
        ]

    def __str__(self):
        return f"{self.order_number} — {self.full_name}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = f"TEE-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    @property
    def total_items(self):
        return sum(i.quantity for i in self.items.all())

    @property
    def status_color(self):
        return {
            'pending': '#d97706', 'confirmed': '#2563eb', 'processing': '#7c3aed',
            'shipped': '#0891b2', 'delivered': '#16a34a', 'cancelled': '#dc2626',
        }.get(self.status, '#6b7280')


class OrderItem(models.Model):
    """A single product+size line within an order (snapshot at purchase time)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(
        'shop.Product', on_delete=models.SET_NULL, null=True, blank=True, related_name='order_items',
    )
    product_name = models.CharField(max_length=255)
    size = models.CharField(max_length=10)
    quantity = models.PositiveIntegerField(default=1)
    unit_price_gnf = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    subtotal_gnf = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        ordering = ['product_name', 'size']

    def __str__(self):
        return f"{self.product_name} (size {self.size}) × {self.quantity}"

    def save(self, *args, **kwargs):
        self.subtotal_gnf = (self.unit_price_gnf or Decimal('0')) * self.quantity
        super().save(*args, **kwargs)
