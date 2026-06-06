from django.shortcuts import render
from shop.models import Product, Brand

def home(request):
    products = Product.objects.select_related('category', 'brand').prefetch_related('images')
    featured_products = products.filter(is_popular=True)[:4]
    product_grid = products.all()[:8]
    new_products = products.filter(is_new=True)[:4]
    best_sellers = products.filter(is_popular=True)[:4]
    brands = Brand.objects.all()

    if not featured_products:
        featured_products = product_grid[:4]
    if not new_products:
        new_products = product_grid[:4]
    if not best_sellers:
        best_sellers = product_grid[:4]

    return render(request, 'pages/home.html', {
        'featured_products': featured_products,
        'product_grid': product_grid,
        'new_products': new_products,
        'best_sellers': best_sellers,
        'brands': brands,
    })

def about(request):   return render(request, 'pages/about.html')
def contact(request): return render(request, 'pages/contact.html')
def faq(request):     return render(request, 'pages/faq.html')
def terms(request):   return render(request, 'pages/terms.html')
def privacy(request): return render(request, 'pages/privacy.html')
def blog(request):    return render(request, 'pages/blog.html')
