from urllib.parse import quote

from django.conf import settings
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render

from shop.models import Product, Brand
from accounts.email_utils import send_contact_form_email
from .forms import ContactForm


def whatsapp_redirect(request):
    """Server-side redirect to WhatsApp.

    The frontend only ever links to this internal route, so the real wa.me URL
    and the business number stay out of the page source. The destination host is
    always wa.me (with our own number), so the user-supplied ``text``/``product``
    only controls the prefilled message — there is no open-redirect surface.

    Optional query params:
        text     -- prefilled message (overrides the default)
        product  -- product name; builds an "interested in ..." message
        share    -- if truthy, use the no-recipient share intent (wa.me/?text=)
    """
    text = request.GET.get('text', '').strip()
    product = request.GET.get('product', '').strip()
    if not text:
        if product:
            text = f"Hello, I'm interested in the {product}."
        else:
            text = settings.WHATSAPP_MESSAGE

    if request.GET.get('share'):
        target = f"https://wa.me/?text={quote(text)}"
    else:
        target = f"https://wa.me/{settings.WHATSAPP_NUMBER}?text={quote(text)}"
    return HttpResponseRedirect(target)

def home(request):
    products = Product.objects.filter(is_active=True).select_related('category', 'brand').prefetch_related('images')
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

def about(request):
    return render(request, 'pages/about.html')


def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            sent = send_contact_form_email(
                full_name=cd['full_name'],
                email=cd['email'],
                phone=cd.get('phone', ''),
                subject=cd['subject'],
                message=cd['message'],
                request=request,
            )
            if sent:
                messages.success(request, 'Thanks for reaching out — we’ll get back to you shortly.')
            else:
                messages.success(request, 'Thanks for your message — we’ll be in touch soon.')
            return redirect('contact')
    else:
        form = ContactForm()

    from django.conf import settings
    digits = ''.join(ch for ch in settings.BUSINESS_PHONE if ch.isdigit())
    return render(request, 'pages/contact.html', {
        'form': form,
        'business_phone': settings.BUSINESS_PHONE,
        'business_email': settings.BUSINESS_EMAIL,
        'whatsapp_number': digits,
    })
def faq(request):
    faqs = [
        {'q': 'How long does shipping take?',
         'a': 'Orders within Conakry are typically delivered within 1–2 business days. '
              'Deliveries elsewhere in Guinea take 2–5 business days. You’ll receive tracking details once your order ships.'},
        {'q': 'What payment methods do you accept?',
         'a': 'We accept Orange Money, MTN Mobile Money, cash on delivery (where available) and bank transfer. '
              'All payment details are handled securely.'},
        {'q': 'What is your return & refund policy?',
         'a': 'You can return unworn items in their original packaging within 7 days of delivery. '
              'Once we receive and inspect the item, your refund or exchange is processed promptly.'},
        {'q': 'Are your products authentic?',
         'a': 'Yes — 100%. Every pair we sell is genuine and carefully sourced. We never sell replicas.'},
        {'q': 'How do I track my order?',
         'a': 'After your order ships, we send you a tracking reference by email or WhatsApp. '
              'You can also reach our team any time for an update.'},
        {'q': 'How do I choose the right size?',
         'a': 'Each product page lists available sizes (EU 38–48). If you’re between sizes or unsure, '
              'message us and we’ll help you find the best fit.'},
    ]
    return render(request, 'pages/faq.html', {'faqs': faqs})
def terms(request):   return render(request, 'pages/terms.html')
def privacy(request):
    from django.conf import settings
    return render(request, 'pages/privacy.html', {'BUSINESS_EMAIL': settings.BUSINESS_EMAIL})
def blog(request):    return render(request, 'pages/blog.html')
