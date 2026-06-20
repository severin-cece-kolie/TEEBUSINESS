from django.contrib import admin
from django.utils.html import format_html

from django.utils.text import slugify

from unfold.admin import ModelAdmin, TabularInline
from import_export.admin import ImportExportModelAdmin
from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget, IntegerWidget
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
    ordering = ('size',)
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


class StockStatusFilter(admin.SimpleListFilter):
    """Filter variants by availability (in / low / out of stock)."""
    title = 'disponibilité'
    parameter_name = 'availability'

    def lookups(self, request, model_admin):
        return (('in', 'En stock'), ('low', 'Stock faible'), ('out', 'Rupture'))

    def queryset(self, request, queryset):
        from django.db.models import F
        if self.value() == 'out':
            return queryset.filter(quantity=0)
        if self.value() == 'low':
            return queryset.filter(quantity__gt=0, quantity__lte=F('low_stock_threshold'))
        if self.value() == 'in':
            return queryset.filter(quantity__gt=F('low_stock_threshold'))
        return queryset


def _unique_category_slug(name):
    base = slugify(name) or 'categorie'
    slug, i = base, 1
    while Category.objects.filter(slug=slug).exists():
        i += 1
        slug = f'{base}-{i}'
    return slug


class ProductSizeImportResource(resources.ModelResource):
    """
    Variant-level import. One row per pointure with columns:
        Produit | Marque | Catégorie | Prix | Pointure | Stock
    Creates/updates the Product (+ Brand/Category) then sets the size's stock.
    """
    product = fields.Field(attribute='product', column_name='Produit',
                           widget=ForeignKeyWidget(Product, 'name'))
    size = fields.Field(attribute='size', column_name='Pointure')
    quantity = fields.Field(attribute='quantity', column_name='Stock', widget=IntegerWidget())

    class Meta:
        model = ProductSize
        import_id_fields = ('product', 'size')
        fields = ('product', 'size', 'quantity')
        skip_unchanged = True
        report_skipped = False

    @staticmethod
    def _get(row, *names):
        for n in names:
            for k in row.keys():
                if k and k.strip().lower() == n.lower():
                    return row[k]
        return None

    def before_import(self, dataset, **kwargs):
        # Don't email subscribers a "new arrival" for every imported product.
        from django.conf import settings
        self._prev_notif = getattr(settings, 'PRODUCT_NOTIFICATIONS_ENABLED', True)
        settings.PRODUCT_NOTIFICATIONS_ENABLED = False
        return super().before_import(dataset, **kwargs)

    def after_import(self, dataset, result, **kwargs):
        from django.conf import settings
        settings.PRODUCT_NOTIFICATIONS_ENABLED = getattr(self, '_prev_notif', True)
        return super().after_import(dataset, result, **kwargs)

    def before_import_row(self, row, **kwargs):
        name = (self._get(row, 'Produit', 'Product', 'name') or '').strip()
        if not name:
            return
        brand_name = (self._get(row, 'Marque', 'Brand') or '').strip()
        cat_name = (self._get(row, 'Catégorie', 'Categorie', 'Category') or '').strip()
        price = self._get(row, 'Prix', 'Price', 'price_gnf')
        size = str(self._get(row, 'Pointure', 'Size', 'size') or '').strip()

        cat = None
        if cat_name:
            cat, _ = Category.objects.get_or_create(
                name=cat_name, defaults={'slug': _unique_category_slug(cat_name)})
        brand = None
        if brand_name:
            brand, _ = Brand.objects.get_or_create(name=brand_name)

        defaults = {'is_active': True}
        if cat:
            defaults['category'] = cat
        if brand:
            defaults['brand'] = brand
        if price not in (None, ''):
            defaults['price_gnf'] = price
        else:
            defaults['price_gnf'] = 0

        product, created = Product.objects.get_or_create(name=name, defaults=defaults)
        if not created:
            changed = False
            if cat and product.category_id != cat.id:
                product.category = cat; changed = True
            if brand and product.brand_id != brand.id:
                product.brand = brand; changed = True
            if price not in (None, '') and str(product.price_gnf) != str(price):
                product.price_gnf = price; changed = True
            if changed:
                product.save()

        # Make sure the size row exists so import_id_fields matches & updates it.
        if size:
            ProductSize.objects.get_or_create(product=product, size=size, defaults={'quantity': 0})

        # Normalise the lookup columns the declared fields read from.
        row['Produit'] = product.name
        row['Pointure'] = size


@admin.register(ProductSize)
class ProductSizeAdmin(ImportExportModelAdmin, ModelAdmin):
    """Quick bulk stock editing + variant CSV/XLSX import."""
    resource_class = ProductSizeImportResource
    formats = [base_formats.CSV, base_formats.XLSX]
    list_display = ('product', 'size', 'quantity', 'low_stock_threshold', 'stock_badge')
    list_filter = (StockStatusFilter, 'product__category', 'product__brand', 'size')
    list_editable = ('quantity', 'low_stock_threshold')
    search_fields = ('product__name',)
    autocomplete_fields = ('product',)
    list_select_related = ('product', 'product__category')
    list_per_page = 50
    ordering = ('product__name', 'size')

    @admin.display(description='Statut')
    def stock_badge(self, obj):
        colors = {'in_stock': '#16a34a', 'low_stock': '#d97706', 'out_of_stock': '#dc2626'}
        labels = {'in_stock': 'En stock', 'low_stock': 'Faible', 'out_of_stock': 'Rupture'}
        s = obj.stock_status
        return format_html('<b style="color:{}">{}</b>', colors.get(s, '#666'), labels.get(s, s))

    # ── Compact stock grid (Produit | 38 … 48), editable in bulk ──
    GRID_SIZES = [str(s) for s in range(38, 49)]

    def get_urls(self):
        from django.urls import path
        custom = [
            path('grid/', self.admin_site.admin_view(self.stock_grid_view),
                 name='shop_productsize_grid'),
        ]
        return custom + super().get_urls()

    def stock_grid_view(self, request):
        from django.contrib import messages
        from django.core.paginator import Paginator
        from django.db.models import F, Q, Sum
        from django.shortcuts import redirect, render

        if request.method == 'POST':
            updates = {}
            for key, val in request.POST.items():
                if not key.startswith('qty_'):
                    continue
                try:
                    _, pid, size = key.split('_', 2)
                    updates[(pid, size)] = max(0, int(val or 0))
                except (ValueError, TypeError):
                    continue
            changed = []
            if updates:
                rows = ProductSize.objects.filter(product_id__in={pid for pid, _ in updates})
                for r in rows:
                    nv = updates.get((str(r.product_id), r.size))
                    if nv is not None and r.quantity != nv:
                        r.quantity = nv
                        changed.append(r)
                if changed:
                    ProductSize.objects.bulk_update(changed, ['quantity'])
            messages.success(request, f'{len(changed)} pointure(s) mise(s) à jour.')
            return redirect(request.get_full_path())

        qs = Product.objects.select_related('brand', 'category').prefetch_related('sizes')
        q = request.GET.get('q', '').strip()
        brand = request.GET.get('brand', '').strip()
        category = request.GET.get('category', '').strip()
        avail = request.GET.get('availability', '').strip()
        if q:
            qs = qs.filter(name__icontains=q)
        if brand:
            qs = qs.filter(brand_id=brand)
        if category:
            qs = qs.filter(category__slug=category)
        if avail == 'out':
            qs = qs.annotate(st=Sum('sizes__quantity')).filter(Q(st=0) | Q(st__isnull=True))
        elif avail == 'low':
            qs = qs.filter(sizes__quantity__gt=0,
                           sizes__quantity__lte=F('sizes__low_stock_threshold')).distinct()
        qs = qs.order_by('name')

        page = Paginator(qs, 25).get_page(request.GET.get('page'))
        grid = []
        for p in page:
            smap = {s.size: s.quantity for s in p.sizes.all()}
            grid.append({'product': p, 'cells': [(sz, smap.get(sz)) for sz in self.GRID_SIZES]})

        ctx = {
            **self.admin_site.each_context(request),
            'title': 'Grille de stock', 'sizes': self.GRID_SIZES, 'grid': grid, 'page': page,
            'brands': Brand.objects.all(), 'categories': Category.objects.all(),
            'q': q, 'sel_brand': brand, 'sel_category': category, 'sel_avail': avail,
            'opts': self.model._meta,
        }
        return render(request, 'admin/stock_grid.html', ctx)
