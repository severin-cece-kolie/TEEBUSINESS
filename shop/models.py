from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils.text import slugify

IMAGE_EXTENSIONS = ['jpg', 'jpeg', 'png', 'webp', 'gif']

class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)

    class Meta:
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name

class Brand(models.Model):
    name = models.CharField(max_length=100)
    
    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, null=True, blank=True)
    description = models.TextField(blank=True)
    price_gnf = models.DecimalField(max_digits=12, decimal_places=2)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True)
    is_new = models.BooleanField(default=False)
    is_popular = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True, help_text="Untick to hide this product from the store.")
    discount_percent = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name) or 'product'
            slug = base
            n = 1
            existing = Product.objects.exclude(pk=self.pk)
            while existing.filter(slug=slug).exists():
                n += 1
                slug = f"{base}-{n}"
            self.slug = slug
        super().save(*args, **kwargs)

    @property
    def discounted_price(self):
        if self.discount_percent > 0:
            return float(self.price_gnf) * (1 - self.discount_percent / 100)
        return float(self.price_gnf)

    @property
    def total_stock(self):
        return sum(s.quantity for s in self.sizes.all())

    @property
    def in_stock(self):
        return self.total_stock > 0

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.FileField(
        upload_to='products/',
        validators=[FileExtensionValidator(allowed_extensions=IMAGE_EXTENSIONS)],
        help_text='JPG, PNG, WEBP or GIF.',
    )
    is_primary = models.BooleanField(default=False)
    label = models.CharField(max_length=50, blank=True, help_text="e.g., Front view, Side view")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

class ProductSize(models.Model):
    SIZE_CHOICES = [(str(s), str(s)) for s in range(38, 49)]
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='sizes')
    size = models.CharField(max_length=10, choices=SIZE_CHOICES)
    quantity = models.PositiveIntegerField(default=0)
    low_stock_threshold = models.PositiveIntegerField(default=5)

    def __str__(self):
        return f"{self.product.name} - Size {self.size}"

    @property
    def stock_status(self):
        if self.quantity <= 0:
            return 'out_of_stock'
        if self.quantity <= self.low_stock_threshold:
            return 'low_stock'
        return 'in_stock'
