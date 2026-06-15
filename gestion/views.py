"""Standalone, branded staff management dashboard (/gestion/).

Read-only analytics + list views over the existing models (cart.Order,
shop.Product, accounts.User). Staff-only. CRUD is intentionally delegated to the
Django admin via "edit" links so this stays a focused, fast dashboard.
"""
import csv
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db.models import Count, DecimalField, Q, Sum, Value
from django.db.models.functions import Coalesce, TruncDate, TruncMonth
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone

from cart.models import Order, OrderItem
from shop.models import Category, Product

User = get_user_model()

MONTHS_FR = ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Juin',
             'Juil', 'Aoû', 'Sep', 'Oct', 'Nov', 'Déc']

LOW_STOCK_THRESHOLD = 5

# Staff gate — non-staff are bounced to the public login (which honours ?next=).
staff_required = user_passes_test(lambda u: u.is_active and u.is_staff, login_url='login')


# ── helpers ──────────────────────────────────────────────────────────────────

def gnf(value):
    """Format a GNF amount with thin spaces: 1234567 -> '1 234 567 GNF'."""
    return f"{int(value or 0):,}".replace(',', ' ') + ' GNF'


def pct_change(current, previous):
    """Month-over-month percentage; 0 baseline → +100% if growing else 0%."""
    current, previous = float(current or 0), float(previous or 0)
    if previous:
        return round((current - previous) / previous * 100, 1)
    return 100.0 if current else 0.0


def _last_12_months(today):
    """Return list of (year, month) for the trailing 12 months, oldest first."""
    y, m, out = today.year, today.month, []
    for _ in range(12):
        out.append((y, m))
        m -= 1
        if m == 0:
            m, y = 12, y - 1
    out.reverse()
    return out


def _product_stock_qs():
    return Product.objects.annotate(stock=Coalesce(Sum('sizes__quantity'), Value(0)))


# ── pages ────────────────────────────────────────────────────────────────────

@login_required(login_url='login')
@staff_required
def dashboard(request):
    today = timezone.localdate()
    month_start = today.replace(day=1)
    prev_end = month_start - timedelta(days=1)
    prev_start = prev_end.replace(day=1)

    valid = Order.objects.exclude(status='cancelled')

    # KPI: revenue
    revenue = valid.aggregate(s=Sum('total_gnf'))['s'] or 0
    rev_this = valid.filter(created_at__date__gte=month_start).aggregate(s=Sum('total_gnf'))['s'] or 0
    rev_prev = valid.filter(created_at__date__gte=prev_start,
                            created_at__date__lt=month_start).aggregate(s=Sum('total_gnf'))['s'] or 0

    # KPI: orders
    orders_total = Order.objects.count()
    ord_this = Order.objects.filter(created_at__date__gte=month_start).count()
    ord_prev = Order.objects.filter(created_at__date__gte=prev_start,
                                    created_at__date__lt=month_start).count()

    # KPI: stock
    stock_qs = _product_stock_qs()
    out_of_stock = stock_qs.filter(Q(stock=0) | Q(stock__isnull=True)).count()
    low_stock = stock_qs.filter(stock__gt=0, stock__lte=LOW_STOCK_THRESHOLD).count()

    # KPI: pending
    pending = Order.objects.filter(status='pending').count()
    pending_ratio = round(pending / orders_total * 100) if orders_total else 0

    # Chart: revenue, trailing 90 days (JS slices 7/30/90)
    start90 = today - timedelta(days=89)
    rows = (valid.filter(created_at__date__gte=start90)
            .annotate(d=TruncDate('created_at')).values('d')
            .annotate(rev=Sum('total_gnf')).order_by('d'))
    rev_by_day = {r['d']: float(r['rev'] or 0) for r in rows}
    rev_labels, rev_data = [], []
    for i in range(90):
        d = start90 + timedelta(days=i)
        rev_labels.append(d.strftime('%d/%m'))
        rev_data.append(round(rev_by_day.get(d, 0)))

    # Chart: revenue, trailing 12 months ("1 an" toggle)
    monthly = (valid.annotate(mm=TruncMonth('created_at')).values('mm')
               .annotate(rev=Sum('total_gnf')))
    rev_by_month = {(r['mm'].year, r['mm'].month): float(r['rev'] or 0) for r in monthly}
    m_labels, m_data = [], []
    for (yy, mm) in _last_12_months(today):
        m_labels.append(f"{MONTHS_FR[mm - 1]} {str(yy)[2:]}")
        m_data.append(round(rev_by_month.get((yy, mm), 0)))

    # Chart: operational volume — orders/month, current year
    vol = (Order.objects.filter(created_at__year=today.year)
           .annotate(mm=TruncMonth('created_at')).values('mm').annotate(c=Count('id')))
    vol_by_month = {r['mm'].month: r['c'] for r in vol}
    vol_data = [vol_by_month.get(i, 0) for i in range(1, 13)]

    context = {
        'active': 'dashboard',
        'page_title': 'Tableau de bord',
        # KPIs
        'revenue_display': gnf(revenue),
        'revenue_pct': pct_change(rev_this, rev_prev),
        'orders_total': orders_total,
        'orders_pct': pct_change(ord_this, ord_prev),
        'out_of_stock': out_of_stock,
        'low_stock': low_stock,
        'pending': pending,
        'pending_ratio': pending_ratio,
        # charts
        'rev_labels': rev_labels, 'rev_data': rev_data,
        'rev_month_labels': m_labels, 'rev_month_data': m_data,
        'vol_labels': MONTHS_FR, 'vol_data': vol_data,
        'current_year': today.year,
        # table
        'recent_orders': Order.objects.all()[:7],
    }
    return render(request, 'gestion/dashboard.html', context)


@login_required(login_url='login')
@staff_required
def produits(request):
    q = request.GET.get('q', '').strip()
    cat = request.GET.get('category', '').strip()
    qs = (_product_stock_qs().select_related('category', 'brand')
          .prefetch_related('images').order_by('-created_at'))
    if q:
        qs = qs.filter(name__icontains=q)
    if cat:
        qs = qs.filter(category__slug=cat)

    page = Paginator(qs, 12).get_page(request.GET.get('page'))
    context = {
        'active': 'produits', 'page_title': 'Produits',
        'products': page, 'q': q, 'current_category': cat,
        'categories': Category.objects.all(),
        'total_count': qs.count(),
    }
    return render(request, 'gestion/produits.html', context)


@login_required(login_url='login')
@staff_required
def commandes(request):
    q = request.GET.get('q', '').strip()
    status = request.GET.get('status', '').strip()
    qs = Order.objects.all().order_by('-created_at')
    if status:
        qs = qs.filter(status=status)
    if q:
        qs = qs.filter(Q(order_number__icontains=q) | Q(full_name__icontains=q)
                       | Q(email__icontains=q) | Q(phone__icontains=q))

    page = Paginator(qs, 15).get_page(request.GET.get('page'))
    context = {
        'active': 'commandes', 'page_title': 'Commandes',
        'orders': page, 'q': q, 'current_status': status,
        'statuses': Order.STATUS_CHOICES, 'total_count': qs.count(),
    }
    return render(request, 'gestion/commandes.html', context)


@login_required(login_url='login')
@staff_required
def clients(request):
    q = request.GET.get('q', '').strip()
    qs = (User.objects.filter(is_staff=False)
          .annotate(orders_count=Count('orders', distinct=True),
                    spent=Coalesce(Sum('orders__total_gnf',
                                       filter=~Q(orders__status='cancelled')),
                                   Value(0), output_field=DecimalField()))
          .order_by('-date_joined'))
    if q:
        qs = qs.filter(Q(email__icontains=q) | Q(first_name__icontains=q)
                       | Q(last_name__icontains=q))

    page = Paginator(qs, 15).get_page(request.GET.get('page'))
    context = {
        'active': 'clients', 'page_title': 'Clients',
        'clients': page, 'q': q, 'total_count': qs.count(),
    }
    return render(request, 'gestion/clients.html', context)


@login_required(login_url='login')
@staff_required
def analyses(request):
    today = timezone.localdate()
    valid = Order.objects.exclude(status='cancelled')

    # Revenue, trailing 12 months
    monthly = (valid.annotate(mm=TruncMonth('created_at')).values('mm')
               .annotate(rev=Sum('total_gnf')))
    rev_by_month = {(r['mm'].year, r['mm'].month): float(r['rev'] or 0) for r in monthly}
    rev_labels, rev_data = [], []
    for (yy, mm) in _last_12_months(today):
        rev_labels.append(f"{MONTHS_FR[mm - 1]} {str(yy)[2:]}")
        rev_data.append(round(rev_by_month.get((yy, mm), 0)))

    # New customers, trailing 12 months
    cust = (User.objects.filter(is_staff=False)
            .annotate(mm=TruncMonth('date_joined')).values('mm').annotate(c=Count('id')))
    cust_by_month = {(r['mm'].year, r['mm'].month): r['c'] for r in cust if r['mm']}
    cust_data = [cust_by_month.get((yy, mm), 0) for (yy, mm) in _last_12_months(today)]

    # Orders by status (doughnut)
    by_status = {s: 0 for s, _ in Order.STATUS_CHOICES}
    for r in Order.objects.values('status').annotate(c=Count('id')):
        by_status[r['status']] = r['c']
    status_labels = [label for _, label in Order.STATUS_CHOICES]
    status_data = [by_status[s] for s, _ in Order.STATUS_CHOICES]
    status_colors = ['#d97706', '#2563eb', '#7c3aed', '#0891b2', '#16a34a', '#dc2626']

    # Best sellers (bar)
    best = list(OrderItem.objects.exclude(order__status='cancelled')
                .values('product_name').annotate(qty=Sum('quantity'))
                .order_by('-qty')[:8])
    best_labels = [b['product_name'] for b in best]
    best_data = [b['qty'] for b in best]

    # Revenue by payment method
    pay = {k: 0.0 for k, _ in Order.PAYMENT_CHOICES}
    for r in valid.values('payment_method').annotate(s=Sum('total_gnf')):
        pay[r['payment_method']] = float(r['s'] or 0)
    pay_labels = [label for _, label in Order.PAYMENT_CHOICES]
    pay_data = [round(pay[k]) for k, _ in Order.PAYMENT_CHOICES]

    context = {
        'active': 'analyses', 'page_title': 'Analyses',
        'rev_labels': rev_labels, 'rev_data': rev_data,
        'cust_labels': rev_labels, 'cust_data': cust_data,
        'status_labels': status_labels, 'status_data': status_data, 'status_colors': status_colors,
        'best_labels': best_labels, 'best_data': best_data,
        'pay_labels': pay_labels, 'pay_data': pay_data,
    }
    return render(request, 'gestion/analyses.html', context)


@login_required(login_url='login')
@staff_required
def rapports(request):
    today = timezone.localdate()
    month_start = today.replace(day=1)
    year_start = today.replace(month=1, day=1)
    valid = Order.objects.exclude(status='cancelled')

    def block(qs):
        agg = qs.aggregate(rev=Sum('total_gnf'), c=Count('id'))
        return {'revenue': gnf(agg['rev']), 'count': agg['c'] or 0}

    summary = [
        ("Aujourd'hui", block(valid.filter(created_at__date=today))),
        ('Ce mois-ci', block(valid.filter(created_at__date__gte=month_start))),
        ('Cette année', block(valid.filter(created_at__date__gte=year_start))),
        ('Tout', block(valid)),
    ]

    by_status = []
    counts = {r['status']: r['c'] for r in Order.objects.values('status').annotate(c=Count('id'))}
    revs = {r['status']: r['s'] for r in Order.objects.values('status').annotate(s=Sum('total_gnf'))}
    for s, label in Order.STATUS_CHOICES:
        by_status.append({'label': label, 'count': counts.get(s, 0),
                          'revenue': gnf(revs.get(s, 0)), 'color': Order(status=s).status_color})

    top_products = [
        {'name': b['product_name'], 'qty': b['qty'], 'revenue': gnf(b['rev'])}
        for b in (OrderItem.objects.exclude(order__status='cancelled')
                  .values('product_name')
                  .annotate(qty=Sum('quantity'), rev=Sum('subtotal_gnf'))
                  .order_by('-qty')[:10])
    ]

    low_stock = (_product_stock_qs().filter(stock__lte=LOW_STOCK_THRESHOLD)
                 .select_related('category').order_by('stock')[:15])

    context = {
        'active': 'rapports', 'page_title': 'Rapports',
        'summary': summary, 'by_status': by_status,
        'top_products': top_products, 'low_stock': low_stock,
    }
    return render(request, 'gestion/rapports.html', context)


@login_required(login_url='login')
@staff_required
def parametres(request):
    from django.conf import settings as dj
    context = {
        'active': 'parametres', 'page_title': 'Paramètres',
        'cfg': {
            'business_name': getattr(dj, 'BUSINESS_NAME', ''),
            'business_email': getattr(dj, 'BUSINESS_EMAIL', ''),
            'business_phone': getattr(dj, 'BUSINESS_PHONE', ''),
            'whatsapp': getattr(dj, 'WHATSAPP_NUMBER', ''),
            'tiktok': getattr(dj, 'SOCIAL_TIKTOK', ''),
            'facebook': getattr(dj, 'SOCIAL_FACEBOOK', ''),
            'shipping': gnf(getattr(dj, 'SHIPPING_COST_GNF', 0)),
            'tax': f"{getattr(dj, 'TAX_RATE_PERCENT', 0)} %",
            'email_backend': getattr(dj, 'EMAIL_BACKEND', ''),
        },
    }
    return render(request, 'gestion/parametres.html', context)


# ── CSV exports ──────────────────────────────────────────────────────────────

@login_required(login_url='login')
@staff_required
def export_orders_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="commandes.csv"'
    w = csv.writer(response)
    w.writerow(['N° commande', 'Client', 'Email', 'Téléphone', 'Statut',
                'Paiement', 'Total (GNF)', 'Date'])
    for o in Order.objects.all().order_by('-created_at'):
        w.writerow([o.order_number, o.full_name, o.email, o.phone,
                    o.get_status_display(), o.get_payment_method_display(),
                    int(o.total_gnf), o.created_at.strftime('%Y-%m-%d %H:%M')])
    return response


@login_required(login_url='login')
@staff_required
def export_products_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="produits.csv"'
    w = csv.writer(response)
    w.writerow(['Produit', 'Catégorie', 'Prix (GNF)', 'Stock', 'Actif'])
    for p in _product_stock_qs().select_related('category').order_by('name'):
        w.writerow([p.name, p.category.name if p.category_id else '',
                    int(p.price_gnf), p.stock, 'Oui' if p.is_active else 'Non'])
    return response
