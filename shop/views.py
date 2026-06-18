from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.utils.http import url_has_allowed_host_and_scheme

from .models import Product, Category, Brand
from .pagination import paginate


def catalog(request):
    products = Product.objects.active_listing()
    categories = Category.objects.all()
    brands = Brand.objects.all()

    category_slug = request.GET.get('category', '').strip()
    brand_id = request.GET.get('brand', '').strip()
    search_q = request.GET.get('q', '').strip()

    if category_slug:
        products = products.filter(category__slug=category_slug)
    if brand_id:
        products = products.filter(brand_id=brand_id)
    if search_q:
        products = products.filter(name__icontains=search_q)

    page, page_range = paginate(request, products)

    return render(request, 'shop/catalog.html', {
        'products': page,
        'page_range': page_range,
        'categories': categories,
        'brands': brands,
        'selected_category': category_slug,
        'selected_brand': brand_id,
        'search_q': search_q,
    })


def product_detail(request, id):
    product = get_object_or_404(
        Product.objects.select_related('category', 'brand').prefetch_related('images', 'sizes'),
        id=id, is_active=True,
    )
    similar = Product.objects.filter(
        category=product.category, is_active=True,
    ).exclude(id=id)[:4]
    return render(request, 'shop/product_detail.html', {
        'product': product,
        'similar_products': similar,
        'share_url': request.build_absolute_uri(),
    })


def search(request):
    return catalog(request)


def set_currency(request):
    """
    View to switch currency and store it in session.
    """
    currency = request.GET.get('currency', 'GNF')
    next_url = request.GET.get('next') or '/'
    
    if currency in ['GNF', 'EUR', 'USD']:
        request.session['currency'] = currency

    if not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        next_url = '/'
    return HttpResponseRedirect(next_url)
