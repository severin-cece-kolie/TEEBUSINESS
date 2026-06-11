def cart_processor(request):
    """Expose the total number of items (summed quantities) for the header badge."""
    cart = request.session.get('cart', {})
    try:
        total_qty = sum(int(q) for q in cart.values())
    except (TypeError, ValueError):
        total_qty = 0
    return {'cart_count': total_qty}
