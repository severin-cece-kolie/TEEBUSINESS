from django.contrib import admin
from django.utils.html import format_html

from unfold.admin import ModelAdmin, TabularInline
from import_export.admin import ImportExportModelAdmin
from import_export import resources
from import_export.formats import base_formats

from teebusiness_core.admin_exports import export_pdf_response
from .models import Category, Brand, Product, ProductImage, ProductSize

EXPORT_FORMATS = [base_formats.CSV, base_formats.XLSX, base_formats.JSON]


class ProductImageInline(TabularInline):
    model = ProductImage
    extra = 1
    max_num = 5  # Up to 5 photos per product
    fields = ('image', 'label', 'is_primary', 'order')


class ProductSizeInline(TabularInline):
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
        return format_html('<b style="color:{}">{}</b>', colors.get(status, '#666'), labels.get(status, status))


@admin.register(Category)
class CategoryAdmin(ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Brand)
class BrandAdmin(ModelAdmin):
    list_display = ('name',)


class ProductResource(resources.ModelResource):
    class Meta:
        model = Product
        fields = ('id', 'name', 'category__name', 'brand__name', 'price_gnf',
                  'discount_percent', 'is_active', 'is_new', 'is_popular')
        export_order = fields


@admin.action(description='Exporter la sélection en PDF')
def export_products_pdf(modeladmin, request, queryset):
    cols = ['Produit', 'Catégorie', 'Prix (GNF)', 'Stock', 'Actif']
    rows = [[
        p.name,
        p.category.name if p.category_id else '',
        f'{int(p.price_gnf):,}'.replace(',', ' '),
        p.total_stock,
        'Oui' if p.is_active else 'Non',
    ] for p in queryset.select_related('category').prefetch_related('sizes')]
    return export_pdf_response('Produits TEEBUSINESS', cols, rows, 'produits.pdf',
                               subtitle=f'{queryset.count()} produit(s)')


@admin.register(Product)
class ProductAdmin(ImportExportModelAdmin, ModelAdmin):
    resource_class = ProductResource
    formats = EXPORT_FORMATS
    list_display = ('name', 'category', 'brand', 'price_gnf', 'total_stock_display', 'is_active', 'is_new', 'is_popular')
    list_filter = ('is_active', 'category', 'brand', 'is_new', 'is_popular')
    list_editable = ('price_gnf', 'is_active')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductImageInline, ProductSizeInline]
    actions = [export_products_pdf]
    fieldsets = (
        (None, {'fields': ('name', 'slug', 'description', 'price_gnf', 'discount_percent')}),
        ('Classification', {'fields': ('category', 'brand', 'is_new', 'is_popular', 'is_active')}),
    )

    @admin.display(description='Total stock')
    def total_stock_display(self, obj):
        return obj.total_stock


@admin.register(ProductSize)
class ProductSizeAdmin(ModelAdmin):
    """Standalone view to manage stock across all products/sizes at once."""
    list_display = ('product', 'size', 'quantity', 'low_stock_threshold', 'stock_status')
    list_filter = ('product__category', 'size')
    list_editable = ('quantity', 'low_stock_threshold')
    search_fields = ('product__name',)
    ordering = ('product__name', 'size')
