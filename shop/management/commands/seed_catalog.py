"""
Seed the initial footwear catalog (categories, products and sizes).

Idempotent: safe to run multiple times — existing records are never
duplicated. Images are NOT attached (admins upload them later).

Usage:
    python manage.py seed_catalog
"""

from decimal import Decimal

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from shop.models import Category, Product, ProductSize

# Sizes every product is created with (stock starts at 0).
SIZES = ['38', '39', '40', '41', '42', '43', '44', '45', '46', '47', '48']

# Placeholder price — administrators adjust per product from Django Admin.
DEFAULT_PRICE = Decimal('150000')

CATALOG = {
    'YEEZY SLIDE': [
        'Adidas Yeezy Slide Azure',
        'Adidas Yeezy Slide Flax',
        'Adidas Yeezy Slide Granite',
        'Adidas Yeezy Slide Onyx',
        'Adidas Yeezy Slide Resin',
        'Adidas Yeezy Slide Salt',
        'Adidas Yeezy Slide Slate Marine',
    ],
    'BIRKENSTOCK': [
        'Birkenstock Color',
        'Birkenstock Kaki',
        'Birkenstock Back White',
        'Birkenstock Bleu Ciel',
        'Birkenstock Choco Clair',
        'Birkenstock Chocolat',
        'Birkenstock Gris Foncé',
        'Birkenstock Noir',
        'Birkenstock Salt',
    ],
}


class Command(BaseCommand):
    help = 'Insert the initial catalog (categories, products, sizes) without duplicates.'

    @transaction.atomic
    def handle(self, *args, **options):
        cat_created = prod_created = size_created = 0

        # Don't email subscribers about seeded products — this is bulk setup,
        # not a real "new arrival". The signal reads this flag synchronously.
        previous_flag = getattr(settings, 'PRODUCT_NOTIFICATIONS_ENABLED', True)
        settings.PRODUCT_NOTIFICATIONS_ENABLED = False
        try:
            for category_name, product_names in CATALOG.items():
                category, made = Category.objects.get_or_create(
                    name=category_name,
                    defaults={'slug': self._unique_category_slug(category_name)},
                )
                cat_created += int(made)
                self.stdout.write(('  + ' if made else '  · ') + f'Category: {category_name}')

                for product_name in product_names:
                    product, made = Product.objects.get_or_create(
                        name=product_name,
                        defaults={
                            'category': category,
                            'description': f'{product_name}. Premium footwear by TEEBUSINESS.',
                            'price_gnf': DEFAULT_PRICE,
                            'is_active': True,
                            'is_new': True,
                        },
                    )
                    prod_created += int(made)

                    # Keep the product under the right category even if it
                    # pre-existed without one.
                    if not made and product.category_id != category.id:
                        product.category = category
                        product.save(update_fields=['category'])

                    # Create the full size run (quantity defaults to 0).
                    for size in SIZES:
                        _, s_made = ProductSize.objects.get_or_create(
                            product=product,
                            size=size,
                            defaults={'quantity': 0},
                        )
                        size_created += int(s_made)

                    self.stdout.write(('    + ' if made else '    · ') + product_name)
        finally:
            settings.PRODUCT_NOTIFICATIONS_ENABLED = previous_flag

        self.stdout.write(self.style.SUCCESS(
            f'\nDone. Categories +{cat_created}, Products +{prod_created}, Sizes +{size_created}. '
            f'(Existing records were left untouched.)'
        ))

    @staticmethod
    def _unique_category_slug(name):
        from django.utils.text import slugify
        base = slugify(name) or 'category'
        slug = base
        n = 1
        while Category.objects.filter(slug=slug).exists():
            n += 1
            slug = f'{base}-{n}'
        return slug
