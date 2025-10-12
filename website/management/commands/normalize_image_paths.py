from django.core.management.base import BaseCommand
from website.models import cartOrder, Order
from django.conf import settings
from urllib.parse import urlparse

class Command(BaseCommand):
    help = 'Dry-run or apply normalization of image paths for cartOrder.image and Order.image (strip leading media/ or /media/)'

    def add_arguments(self, parser):
        parser.add_argument('--apply', action='store_true', help='Apply fixes to the database')

    def handle(self, *args, **options):
        apply_changes = options['apply']
        media_prefix = (settings.MEDIA_URL.lstrip('/') if getattr(settings, 'MEDIA_URL','').startswith('/') else settings.MEDIA_URL) or 'media'

        def normalize_value(val):
            if not val:
                return val
            v = val.strip()
            # If full URL, extract path
            if v.startswith('http://') or v.startswith('https://'):
                v = urlparse(v).path or v
            # strip leading slashes
            while v.startswith('/'):
                v = v[1:]
            # remove leading media_prefix
            if media_prefix and v.startswith(media_prefix):
                v = v[len(media_prefix):]
            # final strip
            while v.startswith('/'):
                v = v[1:]
            return v

        # Process cartOrder
        changed = 0
        total = 0
        for item in cartOrder.objects.all():
            total += 1
            orig = item.image or ''
            new = normalize_value(orig)
            if new != (orig or ''):
                self.stdout.write(f"cartOrder id={item.id}: '{orig}' -> '{new}'")
                changed += 1
                if apply_changes:
                    item.image = new
                    item.save()
        self.stdout.write(f"cartOrder: processed {total} rows, to-change {changed}")

        # Process Order image field (ImageField)
        changed = 0
        total = 0
        for o in Order.objects.all():
            total += 1
            orig = o.image.name if getattr(o.image, 'name', None) else (o.image or '')
            new = normalize_value(orig)
            if new != (orig or ''):
                self.stdout.write(f"Order id={o.id}: '{orig}' -> '{new}'")
                changed += 1
                if apply_changes:
                    # Assign to ImageField: set name (relative path)
                    o.image.name = new
                    o.save()
        self.stdout.write(f"Order: processed {total} rows, to-change {changed}")

        if not apply_changes:
            self.stdout.write(self.style.WARNING('Dry run complete. Use --apply to make changes.'))
        else:
            self.stdout.write(self.style.SUCCESS('Normalization applied.'))
