import os
import django
import random
from django.utils.text import slugify

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'teebusiness_core.settings')
django.setup()

from shop.models import Category, Brand, Product, ProductImage, ProductSize

def seed_data():
    print("🧹 Cleaning database...")
    ProductSize.objects.all().delete()
    ProductImage.objects.all().delete()
    Product.objects.all().delete()
    Brand.objects.all().delete()
    Category.objects.all().delete()

    print("🏷️ Creating Categories...")
    cat_yeezy = Category.objects.create(name="Yeezy Slide", slug="yeezy-slide")
    cat_birken = Category.objects.create(name="Birkenstock", slug="birkenstock")

    print("👟 Creating Brands...")
    brand_adidas = Brand.objects.create(name="Adidas")
    brand_birken = Brand.objects.create(name="Birkenstock")

    yeezy_models = [
        "Slide Azure", "Slide Flax", "Slide Granite", 
        "Slide Onyx", "Slide Resin", "Slide Salt", "Slide Slate Marine"
    ]

    birken_models = [
        "Arizona White", "Arizona Black", "Arizona Khaki",
        "Boston Blue", "Boston Cocoa", "Boston Salt"
    ]

    sizes_list = [str(s) for s in range(38, 49)]

    def create_shoe(name, category, brand, is_pop=False):
        # We'll use a placeholder for the image to avoid actually missing files
        p = Product.objects.create(
            name=f"{brand.name} {name}",
            description=f"Authentic {name} from {brand.name}. Premium materials and unmatched comfort.",
            price_gnf=random.choice([850000, 950000, 1100000, 1250000]),
            category=category,
            brand=brand,
            is_new=random.choice([True, False]),
            is_popular=is_pop,
            discount_percent=random.choice([0, 0, 10, 15])
        )
        # Create sizes
        for s in sizes_list:
            qty = random.randint(0, 15)
            ProductSize.objects.create(
                product=p,
                size=s,
                quantity=qty,
                low_stock_threshold=3
            )
        # Placeholder Images
        # In a real scenario, we'd upload actual files. 
        # For now, we point to paths that the user will fulfill or use placeholders.
        ProductImage.objects.create(
            product=p,
            image=f"products/{slugify(name)}.jpg",
            is_primary=True,
            label="Front View"
        )
        return p

    print("🌵 Seeding Yeezy...")
    for m in yeezy_models:
        create_shoe(m, cat_yeezy, brand_adidas, is_pop=random.choice([True, False]))

    print("👞 Seeding Birkenstock...")
    for m in birken_models:
        create_shoe(m, cat_birken, brand_birken, is_pop=random.choice([True, False]))

    print("✅ Seed complete! 13 products with full size/stock grids created.")

if __name__ == "__main__":
    seed_data()
