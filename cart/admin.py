from datetime import timedelta

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.db.models import Sum, Q
from django.db.models.functions import TruncDate
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ('product_name', 'size', 'quantity', 'unit_price_gnf', 'subtotal_gnf')
    readonly_fields = ('product_name', 'size', 'quantity', 'unit_price_gnf', 'subtotal_gnf')
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'full_name', 'status_badge', 'payment_method',
                    'total_gnf', 'created_at', 'invoice_link')
    list_filter = ('status', 'payment_method', 'created_at')
    search_fields = ('order_number', 'full_name', 'email', 'phone')
    date_hierarchy = 'created_at'
    inlines = [OrderItemInline]
    readonly_fields = ('order_number', 'user', 'subtotal_gnf', 'shipping_gnf', 'tax_gnf',
                       'total_gnf', 'created_at', 'updated_at', 'invoice_link')
    list_per_page = 25
    actions = ['mark_confirmed', 'mark_processing', 'mark_shipped', 'mark_delivered', 'mark_cancelled']

    fieldsets = (
        ('Order', {'fields': ('order_number', 'status', 'invoice_link', 'created_at', 'updated_at')}),
        ('Customer', {'fields': ('user', 'full_name', 'phone', 'email')}),
        ('Shipping', {'fields': ('city', 'district', 'address')}),
        ('Payment & totals', {'fields': ('payment_method', 'subtotal_gnf', 'shipping_gnf', 'tax_gnf', 'total_gnf')}),
        ('Note', {'fields': ('note',), 'classes': ('collapse',)}),
    )

    @admin.display(description='Status', ordering='status')
    def status_badge(self, obj):
        return format_html(
            '<span style="background:{};color:#fff;padding:3px 10px;border-radius:99px;'
            'font-size:11px;font-weight:700;text-transform:uppercase;">{}</span>',
            obj.status_color, obj.get_status_display())

    @admin.display(description='Invoice')
    def invoice_link(self, obj):
        if not obj.pk:
            return '—'
        url = reverse('order_invoice', args=[obj.order_number])
        return format_html('<a href="{}" target="_blank">Print</a>', url)

    # --- Quick status actions ---
    def _set_status(self, request, queryset, status):
        updated = queryset.update(status=status)
        self.message_user(request, f'{updated} order(s) marked as {status}.')

    @admin.action(description='Mark as Confirmed')
    def mark_confirmed(self, request, queryset): self._set_status(request, queryset, 'confirmed')

    @admin.action(description='Mark as Processing')
    def mark_processing(self, request, queryset): self._set_status(request, queryset, 'processing')

    @admin.action(description='Mark as Shipped')
    def mark_shipped(self, request, queryset): self._set_status(request, queryset, 'shipped')

    @admin.action(description='Mark as Delivered')
    def mark_delivered(self, request, queryset): self._set_status(request, queryset, 'delivered')

    @admin.action(description='Mark as Cancelled')
    def mark_cancelled(self, request, queryset): self._set_status(request, queryset, 'cancelled')


# ─────────────────────────────────────────────────────────────
# Admin dashboard — inject stats/analytics into the admin index.
# ─────────────────────────────────────────────────────────────

def get_dashboard_stats(request):
    from shop.models import Product
    User = get_user_model()

    today = timezone.localdate()
    month_start = today.replace(day=1)
    paid = Order.objects.exclude(status='cancelled')

    revenue = paid.aggregate(s=Sum('total_gnf'))['s'] or 0
    today_orders = Order.objects.filter(created_at__date=today).count()
    month_orders = Order.objects.filter(created_at__date__gte=month_start).count()
    products_sold = (OrderItem.objects.exclude(order__status='cancelled')
                     .aggregate(s=Sum('quantity'))['s'] or 0)
    out_of_stock = (Product.objects.annotate(stock=Sum('sizes__quantity'))
                    .filter(Q(stock=0) | Q(stock__isnull=True)).count())
    new_customers = User.objects.filter(date_joined__date__gte=month_start, is_staff=False).count()

    # Daily revenue — last 14 days
    start = today - timedelta(days=13)
    rows = (paid.filter(created_at__date__gte=start)
            .annotate(d=TruncDate('created_at')).values('d')
            .annotate(rev=Sum('total_gnf')).order_by('d'))
    rev_by_day = {r['d']: float(r['rev'] or 0) for r in rows}
    labels, data = [], []
    for i in range(14):
        d = start + timedelta(days=i)
        labels.append(d.strftime('%d %b'))
        data.append(rev_by_day.get(d, 0))

    best_sellers = list(
        OrderItem.objects.exclude(order__status='cancelled')
        .values('product_name')
        .annotate(qty=Sum('quantity'), rev=Sum('subtotal_gnf'))
        .order_by('-qty')[:5]
    )

    revenue_display = f"{int(revenue):,}".replace(',', ' ') + ' GNF'

    return {'dash': {
        'revenue': revenue, 'revenue_display': revenue_display,
        'today_orders': today_orders, 'month_orders': month_orders,
        'products_sold': products_sold, 'out_of_stock': out_of_stock,
        'new_customers': new_customers, 'chart_labels': labels, 'chart_data': data,
        'best_sellers': best_sellers,
    }}


_original_admin_index = admin.site.index


def _dashboard_index(request, extra_context=None):
    extra_context = extra_context or {}
    try:
        extra_context.update(get_dashboard_stats(request))
    except Exception:
        pass  # never let stats break the admin home
    return _original_admin_index(request, extra_context)


admin.site.index = _dashboard_index
admin.site.index_template = 'admin/index.html'
