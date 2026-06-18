"""Shared pagination helper used by both Home and Shop (no duplicated logic)."""
from django.core.paginator import Paginator

PRODUCTS_PER_PAGE = 12  # divisible by 2 / 3 / 4 → fills every grid breakpoint cleanly


def paginate(request, queryset, per_page=PRODUCTS_PER_PAGE):
    """Return (page, page_range) for a queryset, page number read from ?page=.

    `page_range` is the elided range (ints + '…') for a compact, professional
    page list that scales to any number of pages.
    """
    paginator = Paginator(queryset, per_page)
    page = paginator.get_page(request.GET.get('page'))
    page_range = list(paginator.get_elided_page_range(page.number, on_each_side=1, on_ends=1))
    return page, page_range
