from django.contrib import admin
from django.utils.html import format_html

from .models import Category, Brand, Product, ProductImage, ProductSize


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    max_num = 5  # Up to 5 photos per product
    fields = ('image', 'label', 'is_primary', 'order')


class ProductSizeInline(admin.TabularInline):
    model = ProductSize
    extra = 0
    fields = ('size', 'quantity', 'low_stock_threshold', 'stock_badge')
    readonly_fields = ('stock_badge',)

    @admin.display(description='Status')
    def stock_badge(self, obj):
        if obj.pk is None:
            return '—'
        colors = {'in_stock': '#16a34a', 'low_stock': '#d97706', 'out_of_stock': '#dc2626'}
        labels = {'in_stock': 'In stock', 'low_stock': 'Low stock', 'out_of_stock': 'Out of stock'}
        status = obj.stock_status
        return format_html(
            '<b style="color:{}">{}</b>', colors.get(status, '#666'), labels.get(status, status)
        )


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'brand', 'price_gnf', 'total_stock_display', 'is_active', 'is_new', 'is_popular')
    list_filter = ('is_active', 'category', 'brand', 'is_new', 'is_popular')
    list_editable = ('price_gnf', 'is_active')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductImageInline, ProductSizeInline]
    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'description', 'price_gnf', 'discount_percent')
        }),
        ('Classification', {
            'fields': ('category', 'brand', 'is_new', 'is_popular', 'is_active')
        }),
    )

    @admin.display(description='Total stock')
    def total_stock_display(self, obj):
        return obj.total_stock


@admin.register(ProductSize)
class ProductSizeAdmin(admin.ModelAdmin):
    """Standalone view to manage stock across all products/sizes at once."""
    list_display = ('product', 'size', 'quantity', 'low_stock_threshold', 'stock_status')
    list_filter = ('product__category', 'size')
    list_editable = ('quantity', 'low_stock_threshold')
    search_fields = ('product__name',)
    ordering = ('product__name', 'size')
