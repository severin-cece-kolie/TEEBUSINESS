"""Downscale + recompress existing ProductImage files that are too heavy.

New uploads are optimised automatically in `ProductImage.save()`; this command
backfills images that were uploaded before that, or any oversized files.

    python manage.py optimize_images            # optimise in place
    python manage.py optimize_images --dry-run  # report only
"""
from io import BytesIO

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from shop.models import ProductImage


class Command(BaseCommand):
    help = "Downscale + recompress oversized product images (keeps quality)."

    def add_arguments(self, parser):
        parser.add_argument('--max-side', type=int, default=ProductImage.OPTIMIZE_MAX_SIDE)
        parser.add_argument('--dry-run', action='store_true')

    def handle(self, *args, **opts):
        from PIL import Image, ImageOps

        max_side, dry = opts['max_side'], opts['dry_run']
        done = skipped = saved_kb = 0

        for pi in ProductImage.objects.all():
            try:
                name = (pi.image.name or '').lower()
                if not name or name.endswith(('.gif', '.svg')):
                    skipped += 1
                    continue
                pi.image.open()
                img = ImageOps.exif_transpose(Image.open(pi.image))
                fmt = (img.format or 'JPEG').upper()
                before = pi.image.size
                if max(img.size) <= max_side and before <= ProductImage.OPTIMIZE_SIZE_THRESHOLD:
                    skipped += 1
                    continue

                img.thumbnail((max_side, max_side), Image.LANCZOS)
                params = {'optimize': True}
                if fmt in ('JPEG', 'JPG'):
                    img = img.convert('RGB'); params.update(quality=85, progressive=True); fmt = 'JPEG'
                elif fmt == 'WEBP':
                    params.update(quality=85)
                elif fmt != 'PNG':
                    skipped += 1
                    continue

                buf = BytesIO()
                img.save(buf, format=fmt, **params)
                after = len(buf.getvalue())
                self.stdout.write(f"{pi.image.name}: {before // 1024}KB -> {after // 1024}KB")
                saved_kb += max(0, (before - after) // 1024)

                if not dry:
                    old = pi.image.name
                    pi.image.delete(save=False)          # remove the heavy original
                    pi.image.save(old, ContentFile(buf.getvalue()), save=True)  # reuse the name
                done += 1
            except Exception as exc:
                self.stderr.write(f"skip #{pi.pk}: {exc}")
                skipped += 1

        suffix = ' (dry-run, nothing written)' if dry else f' — saved ~{saved_kb}KB'
        self.stdout.write(self.style.SUCCESS(f"Optimised {done}, skipped {skipped}{suffix}"))
