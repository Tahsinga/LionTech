from django.db import models
from django.conf import settings


class Product(models.Model):
    CATEGORY_CHOICES = [
        ('Mobiles & Accessories', 'Mobiles & Accessories'),
        ('TVs', 'TVs'),
        ('Cameras & Accessories', 'Cameras & Accessories'),
        # Add more as needed
    ]

    CONDITION_CHOICES = [
        ('New', 'New'),
        ('Used', 'Used'),
        ('Refurbished', 'Refurbished'),
    ]

    name = models.CharField(max_length=255)
    image = models.ImageField(upload_to='products/')
    # Additional image slots to ensure each product has at least 4 pictures
    image_2 = models.ImageField(upload_to='products/', blank=True, null=True, default='website/images/default-image.svg')
    image_3 = models.ImageField(upload_to='products/', blank=True, null=True, default='website/images/default-image.svg')
    image_4 = models.ImageField(upload_to='products/', blank=True, null=True, default='website/images/default-image.svg')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=100, choices=CATEGORY_CHOICES)
    available = models.BooleanField(default=True)

    # Additional Gadget-Specific Fields
    brand_model = models.CharField(max_length=255, default='Unknown')
    color = models.CharField(max_length=50, default='Black')
    storage_ram = models.CharField(max_length=50, default='64GB/4GB')
    network = models.CharField(max_length=100, default='4G LTE')
    battery = models.CharField(max_length=100, default='4000mAh')
    camera = models.CharField(max_length=100, default='12MP Rear / 8MP Front')
    screen = models.CharField(max_length=100, default='6.5” LCD')
    processor = models.CharField(max_length=100, default='Snapdragon 680')
    os = models.CharField(max_length=100, default='Android 13')
    accessories = models.CharField(max_length=255, default='Charger, USB Cable')
    condition = models.CharField(max_length=50, choices=CONDITION_CHOICES, default='New')
    warranty = models.CharField(max_length=100, default='No Warranty')
    location = models.CharField(max_length=100, default='Local')
    optional_details = models.TextField(blank=True,default='N/A')

    def __str__(self):
        return f"{self.name} ({self.brand_model})"

    @property
    def brand(self):
        """Return a cleaned brand name for templates.

        Priority:
        - If `brand_model` contains something meaningful (not 'Unknown'/'NA'), try to extract brand token.
        - Otherwise return empty string so templates can hide the field.
        """
        try:
            bm = (self.brand_model or '').strip()
        except Exception:
            return ''

        low = bm.lower()
        # Common placeholders that should be treated as empty
        placeholders = {'unknown', 'n/a', 'na', 'none', 'null', '', '-'}
        if low in placeholders:
            return ''

        # If brand_model looks like 'Brand Model' or 'Brand - Model', take first token
        # Split by common separators
        for sep in [' - ', '-', '/', '|']:
            if sep in bm:
                candidate = bm.split(sep)[0].strip()
                if candidate and candidate.lower() not in placeholders:
                    return candidate

        # As a fallback if brand_model contains multiple words, take the first word
        parts = bm.split()
        if parts:
            if parts[0].lower() not in placeholders:
                return parts[0]

        return ''


class Bundle(models.Model):
    title = models.CharField(max_length=255)
    # Allow bundles without a dedicated image; we'll reference product images instead
    image = models.ImageField(upload_to='bundles/', blank=True, null=True)
    image_2 = models.ImageField(upload_to='bundles/', blank=True, null=True)
    image_3 = models.ImageField(upload_to='bundles/', blank=True, null=True)
    image_4 = models.ImageField(upload_to='bundles/', blank=True, null=True)
    image_desc_1 = models.CharField(max_length=255, blank=True, default='')
    image_desc_2 = models.CharField(max_length=255, blank=True, default='')
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    description = models.TextField(blank=True, default='')
    badge = models.CharField(max_length=50, blank=True, default='')
    # Allow a bundle to reference existing products (optional)
    products = models.ManyToManyField('Product', blank=True, related_name='bundles')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - ${self.price}"

# this it the order  like the history page 
from django.db import models
from django.utils import timezone

class Order(models.Model): 
    DELIVERY_STATUS_CHOICES = [
        ("pending", "Pending"),
        ("delivered", "Delivered"),
        ("shipped", "Shipped"),
    ]

    first_name = models.CharField(max_length=100, default="")
    last_name = models.CharField(max_length=100, default="")
    phone_number = models.CharField(max_length=20, default="N/A")
    location = models.CharField(max_length=255, default="Unknown Location")
    delivery_notes = models.TextField(blank=True, null=True, default="")

    product = models.CharField(max_length=100, default="Unknown Product")
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    image = models.ImageField(upload_to='order_images/', blank=True, null=True)

    order_number = models.CharField(max_length=20, unique=False, blank=True, null=True)
    date = models.DateTimeField(auto_now_add=True)
    delivery_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    delivery_status = models.CharField(
        max_length=20,
        choices=DELIVERY_STATUS_CHOICES,
        default="pending"
    )
    # Link order to a user if available. For anonymous visitors we store a session key
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='orders')
    session_key = models.CharField(max_length=40, blank=True, null=True)


    def save(self, *args, **kwargs):
        if not self.order_number:
            now = timezone.now()
            # Format order_number: e.g. "202-508-111-638"
            self.order_number = f"{now.strftime('%Y')[0:3]}-{now.strftime('%m')}{now.strftime('%d')[0]}-{now.strftime('%d')}{now.strftime('%H')}-{now.strftime('%H')}{now.strftime('%M')}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.product} ({self.order_number})"

    @property
    def expected_delivery_date(self):
        """
        Compute an expected delivery date based on the order `date` and any hints in `delivery_notes`.

        Rules:
        - If `delivery_notes` contains 'tomorrow' -> +1 day
        - If it contains 'next week' or 'week' -> +7 days
        - Otherwise default to +7 days from order date
        """
        from datetime import timedelta

        try:
            base_dt = self.date if self.date else timezone.now()
            base_dt = timezone.localtime(base_dt)
        except Exception:
            base_dt = timezone.localtime(timezone.now())

        notes = (self.delivery_notes or '').lower()
        if 'tomorrow' in notes:
            delta = timedelta(days=1)
        elif 'next week' in notes or 'nextweek' in notes or 'week' in notes:
            delta = timedelta(days=7)
        else:
            delta = timedelta(days=7)

        return (base_dt + delta).date()

class Cart(models.Model):
    # Link to the product being added
    product = models.ForeignKey(Product, on_delete=models.CASCADE)

    # You can add quantity if you want
    quantity = models.PositiveIntegerField(default=1)

    # Optional: timestamp to know when added
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cart item: {self.product.name} (Qty: {self.quantity})"

from django.utils import timezone
from django.db import models

class cartOrder(models.Model):
    product_id = models.IntegerField(default=0)
    name = models.CharField(max_length=255, default="Unknown Product")
    image = models.URLField(max_length=500, blank=True, null=True, default="")
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    category = models.CharField(max_length=100, default="Uncategorized")
    condition = models.CharField(max_length=50, default="N/A")
    added_at = models.DateTimeField(default=timezone.now)  # Default for both old & new
    quantity = models.PositiveIntegerField(default=1)
    # Owner / session key to scope cart items per visitor
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='cart_items')
    session_key = models.CharField(max_length=40, blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.quantity})"
