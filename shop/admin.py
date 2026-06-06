from django.contrib import admin
from .models import Category, Brand, Product, ProductImage, ProductSize

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1

class ProductSizeInline(admin.TabularInline):
    model = ProductSize
    extra = 0

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'brand', 'category', 'price_gnf', 'is_new', 'is_popular')
    list_filter = ('category', 'brand', 'is_new', 'is_popular')
    search_fields = ('name', 'description')
    inlines = [ProductImageInline, ProductSizeInline]
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'price_gnf', 'discount_percent')
        }),
        ('Classification', {
            'fields': ('category', 'brand', 'is_new', 'is_popular')
        }),
    )
