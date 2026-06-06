from django.shortcuts import render, redirect


def _cart_lines(request):
    from shop.models import Product

    cart_items = request.session.get('cart', {})
    items = []
    total_gnf = 0
    for product_id, qty in cart_items.items():
        try:
            product = Product.objects.prefetch_related('images').get(id=int(product_id))
            quantity = max(1, int(qty))
            price = float(product.discounted_price)
            subtotal = price * quantity
            total_gnf += subtotal
            items.append({'product': product, 'qty': quantity, 'subtotal': subtotal})
        except (Product.DoesNotExist, TypeError, ValueError):
            continue
    return items, total_gnf


def cart(request):
    items, total_gnf = _cart_lines(request)
    return render(request, 'cart/cart.html', {'items': items, 'total_gnf': total_gnf})


def add_to_cart(request, product_id):
    cart = request.session.get('cart', {})
    key = str(product_id)
    try:
        qty = max(1, int(request.POST.get('quantity', 1)))
    except (TypeError, ValueError):
        qty = 1
    cart[key] = int(cart.get(key, 0)) + qty
    request.session['cart'] = cart
    request.session.modified = True
    next_url = request.POST.get('next', request.META.get('HTTP_REFERER', '/'))
    return redirect(next_url)


def remove_from_cart(request, product_id):
    cart = request.session.get('cart', {})
    key = str(product_id)
    if key in cart:
        del cart[key]
    request.session['cart'] = cart
    request.session.modified = True
    return redirect('cart')


def update_cart(request, product_id):
    cart = request.session.get('cart', {})
    key = str(product_id)
    try:
        qty = int(request.POST.get('qty', 1))
    except (TypeError, ValueError):
        qty = 1
    if qty <= 0:
        cart.pop(key, None)
    else:
        cart[key] = qty
    request.session['cart'] = cart
    request.session.modified = True
    return redirect('cart')


def checkout(request):
    items, total_gnf = _cart_lines(request)
    return render(request, 'cart/checkout.html', {'items': items, 'total_gnf': total_gnf})
