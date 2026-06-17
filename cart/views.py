from decimal import Decimal, ROUND_HALF_UP

from django.conf import settings
from django.contrib import messages
from django.db import transaction
from django.db.models import F
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from shop.models import Product, ProductSize
from .models import Order, OrderItem


def _checkout_totals(subtotal):
    """Return (shipping, tax, total) as Decimals from a GNF subtotal."""
    subtotal = Decimal(str(subtotal))
    shipping = Decimal('0') if subtotal <= 0 else Decimal(str(settings.SHIPPING_COST_GNF))
    tax = (subtotal * Decimal(str(settings.TAX_RATE_PERCENT)) / Decimal('100')).quantize(
        Decimal('1'), rounding=ROUND_HALF_UP)
    total = subtotal + shipping + tax
    return shipping, tax, total


# ─────────────────────────────────────────────────────────────
# Session cart structure
#   request.session['cart'] = { "<product_id>:<size>": <quantity>, ... }
# Each product+size is its own line — sizes are never merged.
# ─────────────────────────────────────────────────────────────

def _make_key(product_id, size):
    return f"{product_id}:{size}"


def _split_key(key):
    pid, _, size = key.partition(':')
    return pid, size


def _build_cart(request):
    """
    Return (groups, total_gnf, total_qty).

    groups: list of dicts grouped by product, each:
        {'product', 'lines': [{'key','size','qty','available','status',
                                'unit_price','subtotal'}], 'product_subtotal'}
    """
    cart = request.session.get('cart', {})
    grouped = {}
    total_gnf = 0.0
    total_qty = 0

    for key, qty in cart.items():
        pid, size = _split_key(key)
        product = Product.objects.filter(id=pid, is_active=True).prefetch_related('images').first()
        if product is None:
            continue
        size_obj = ProductSize.objects.filter(product_id=pid, size=size).first()
        available = size_obj.quantity if size_obj else 0
        status = size_obj.stock_status if size_obj else 'out_of_stock'

        try:
            quantity = max(1, int(qty))
        except (TypeError, ValueError):
            continue

        unit_price = float(product.discounted_price)
        subtotal = unit_price * quantity
        total_gnf += subtotal
        total_qty += quantity

        group = grouped.setdefault(product.id, {
            'product': product, 'lines': [], 'product_subtotal': 0.0,
        })
        group['lines'].append({
            'key': key,
            'size': size,
            'qty': quantity,
            'available': available,
            'status': status,
            'over_stock': quantity > available,
            'unit_price': unit_price,
            'subtotal': subtotal,
        })
        group['product_subtotal'] += subtotal

    # Stable ordering: product name, then size.
    groups = sorted(grouped.values(), key=lambda g: g['product'].name)
    for g in groups:
        g['lines'].sort(key=lambda l: l['size'])
    return groups, total_gnf, total_qty


def cart(request):
    groups, total_gnf, total_qty = _build_cart(request)
    return render(request, 'cart/cart.html', {
        'groups': groups, 'total_gnf': total_gnf, 'total_qty': total_qty,
    })


def add_to_cart(request, product_id):
    """Add one or more sizes of a product in a single submission."""
    product = get_object_or_404(Product, id=product_id, is_active=True)
    if request.method != 'POST':
        return redirect('product_detail', id=product.id)

    cart = request.session.get('cart', {})
    sizes = {s.size: s for s in product.sizes.all()}

    # Build the requested {size: qty} map. Two input styles are supported:
    #   - single size:  POST 'size' + 'quantity'   (product page pills)
    #   - bulk:          POST 'qty_<size>' per size (multi-size form)
    requested = {}
    if request.POST.get('size'):
        try:
            requested[request.POST['size']] = int(request.POST.get('quantity', 1))
        except (TypeError, ValueError):
            requested[request.POST['size']] = 1
    else:
        for size in sizes:
            try:
                requested[size] = int(request.POST.get(f'qty_{size}', '0'))
            except (TypeError, ValueError):
                requested[size] = 0

    added = 0
    capped = False
    for size, want in requested.items():
        size_obj = sizes.get(size)
        if size_obj is None or want <= 0:
            continue
        if size_obj.quantity <= 0:
            continue  # out of stock — skip silently

        key = _make_key(product.id, size)
        current = int(cart.get(key, 0))
        new_qty = current + want
        if new_qty > size_obj.quantity:
            new_qty = size_obj.quantity
            capped = True
        cart[key] = new_qty
        added += (new_qty - current)

    request.session['cart'] = cart
    request.session.modified = True

    cart_count = sum(int(v) for v in cart.values())

    if added > 0:
        msg = f'Added {added} item{"s" if added != 1 else ""} to your cart.'
        if capped:
            msg += ' Some quantities were limited by available stock.'
        ok = True
    else:
        msg = 'Please choose at least one size that is in stock.'
        ok = False

    # AJAX (Fetch) → JSON for the toast + bell counter. No Django banner message
    # is created on this path, so the green banner no longer appears for adds.
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'ok': ok, 'added': added, 'capped': capped,
                             'message': msg, 'cart_count': cart_count})

    # No-JS fallback: preserve the original Django-messages + redirect behaviour.
    (messages.success if ok else messages.error)(request, msg)
    return redirect('cart')


def update_cart(request):
    """Update the quantity of a single product+size line."""
    if request.method != 'POST':
        return redirect('cart')

    key = request.POST.get('key', '')
    cart = request.session.get('cart', {})
    if key not in cart:
        return redirect('cart')

    try:
        qty = int(request.POST.get('qty', 1))
    except (TypeError, ValueError):
        qty = 1

    if qty <= 0:
        cart.pop(key, None)
        messages.success(request, 'Item removed from your cart.')
    else:
        pid, size = _split_key(key)
        size_obj = ProductSize.objects.filter(product_id=pid, size=size).first()
        available = size_obj.quantity if size_obj else 0
        if available <= 0:
            cart.pop(key, None)
            messages.error(request, 'That size is now out of stock and was removed.')
        else:
            if qty > available:
                qty = available
                messages.success(request, f'Only {available} left in that size — quantity adjusted.')
            cart[key] = qty

    request.session['cart'] = cart
    request.session.modified = True
    return redirect('cart')


def remove_from_cart(request):
    """Remove a single product+size line."""
    if request.method != 'POST':
        return redirect('cart')
    key = request.POST.get('key', '')
    cart = request.session.get('cart', {})
    if key in cart:
        del cart[key]
        request.session['cart'] = cart
        request.session.modified = True
        messages.success(request, 'Item removed from your cart.')
    return redirect('cart')


def checkout(request):
    groups, total_gnf, total_qty = _build_cart(request)
    if not groups:
        messages.error(request, 'Your cart is empty.')
        return redirect('cart')

    shipping, tax, total = _checkout_totals(total_gnf)
    user = request.user if request.user.is_authenticated else None
    prefill = {
        'full_name': (user.get_full_name() if user else '') or (user.first_name if user else ''),
        'phone': getattr(user, 'phone_number', '') or '' if user else '',
        'email': user.email if user else '',
        'city': getattr(user, 'city', '') if user else '',
        'address': getattr(user, 'address', '') if user else '',
    }
    return render(request, 'cart/checkout.html', {
        'groups': groups, 'subtotal_gnf': total_gnf, 'total_qty': total_qty,
        'shipping_gnf': shipping, 'tax_gnf': tax, 'total_gnf': total,
        'tax_rate': settings.TAX_RATE_PERCENT, 'prefill': prefill,
        'payment_choices': Order.PAYMENT_CHOICES,
    })


@transaction.atomic
def place_order(request):
    """Validate input + stock, create the Order, deduct stock, clear the cart."""
    if request.method != 'POST':
        return redirect('checkout')

    cart = request.session.get('cart', {})
    if not cart:
        messages.error(request, 'Your cart is empty.')
        return redirect('cart')

    # --- Customer / shipping fields ---
    fields = {k: request.POST.get(k, '').strip() for k in
              ('full_name', 'phone', 'email', 'city', 'district', 'address', 'payment_method')}
    required = ['full_name', 'phone', 'email', 'city', 'address']
    missing = [f for f in required if not fields[f]]
    if missing or '@' not in fields['email']:
        messages.error(request, 'Please complete all required fields with a valid email.')
        return redirect('checkout')
    if fields['payment_method'] not in dict(Order.PAYMENT_CHOICES):
        fields['payment_method'] = 'cod'

    # --- Validate stock (lock rows) and build line snapshots ---
    line_rows = []
    subtotal = Decimal('0')
    for key, qty in cart.items():
        pid, size = _split_key(key)
        try:
            quantity = max(1, int(qty))
        except (TypeError, ValueError):
            continue

        size_obj = (
            ProductSize.objects.select_for_update()
            .select_related('product')
            .filter(product_id=pid, size=size, product__is_active=True)
            .first()
        )
        if size_obj is None:
            messages.error(request, 'A product in your cart is no longer available. Please review your cart.')
            return redirect('cart')
        if quantity > size_obj.quantity:
            messages.error(request, f'Only {size_obj.quantity} left of {size_obj.product.name} (size {size}). Please adjust your cart.')
            return redirect('cart')

        unit_price = Decimal(str(size_obj.product.discounted_price)).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
        line_rows.append({
            'product': size_obj.product, 'name': size_obj.product.name,
            'size': size, 'qty': quantity, 'unit_price': unit_price,
            'subtotal': unit_price * quantity,
        })
        subtotal += unit_price * quantity

    shipping, tax, total = _checkout_totals(subtotal)

    # --- Create the order ---
    order = Order.objects.create(
        user=request.user if request.user.is_authenticated else None,
        full_name=fields['full_name'], phone=fields['phone'], email=fields['email'],
        city=fields['city'], district=fields['district'], address=fields['address'],
        payment_method=fields['payment_method'], status='pending',
        subtotal_gnf=subtotal, shipping_gnf=shipping, tax_gnf=tax, total_gnf=total,
    )
    for row in line_rows:
        OrderItem.objects.create(
            order=order, product=row['product'], product_name=row['name'],
            size=row['size'], quantity=row['qty'], unit_price_gnf=row['unit_price'],
        )
        ProductSize.objects.filter(product=row['product'], size=row['size']).update(
            quantity=F('quantity') - row['qty'])

    request.session['cart'] = {}
    request.session.modified = True

    return redirect('order_confirmation', order_number=order.order_number)


def order_confirmation(request, order_number):
    order = get_object_or_404(Order.objects.prefetch_related('items'), order_number=order_number)
    return render(request, 'cart/order_complete.html', {'order': order})


def order_invoice(request, order_number):
    order = get_object_or_404(Order.objects.prefetch_related('items'), order_number=order_number)
    return render(request, 'cart/invoice.html', {'order': order})
