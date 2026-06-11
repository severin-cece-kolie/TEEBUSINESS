from django.db import migrations
from django.utils.text import slugify


def backfill_slugs(apps, schema_editor):
    Product = apps.get_model('shop', 'Product')
    used = set(
        Product.objects.exclude(slug__isnull=True).exclude(slug='').values_list('slug', flat=True)
    )
    for product in Product.objects.filter(slug__isnull=True) | Product.objects.filter(slug=''):
        base = slugify(product.name) or 'product'
        slug = base
        n = 1
        while slug in used:
            n += 1
            slug = f"{base}-{n}"
        used.add(slug)
        product.slug = slug
        product.save(update_fields=['slug'])


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0003_product_is_active_product_slug_and_more'),
    ]

    operations = [
        migrations.RunPython(backfill_slugs, noop),
    ]
