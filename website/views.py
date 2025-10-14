from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.core.paginator import Paginator
from datetime import datetime
import json
from decimal import Decimal
from random import sample

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser

from django.conf import settings
import logging

from django.db.models import Q, F, ExpressionWrapper, DecimalField
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import Product, Order, Cart, cartOrder
from .serializers import ProductSerializer, OrderSerializer
from .serializers import BundleSerializer
from .models import Bundle

from .forms import ProductForm

logger = logging.getLogger(__name__)

# ---------------- CART FUNCTIONS ---------------- #

@require_POST
def remove_from_cart(request, product_id):
    # Remove from session-based cart if present
    cart = request.session.get('cart', {})
    product_id_str = str(product_id)
    if product_id_str in cart:
        del cart[product_id_str]
        request.session['cart'] = cart

    # Also remove any persistent cartOrder entries for this product (scope to user/session)
    try:
        session_key = request.session.session_key
        if request.user.is_authenticated:
            qs = cartOrder.objects.filter(product_id=product_id, owner=request.user)
        else:
            qs = cartOrder.objects.filter(product_id=product_id, session_key=session_key)
        deleted_count, _ = qs.delete()
    except Exception:
        # If something goes wrong, still return success=False
        return JsonResponse({'success': False, 'message': 'Failed to remove item from database.'})

    # Compute updated totals to return to client (helps UI update without extra fetch)
    if request.user.is_authenticated:
        cart_items = cartOrder.objects.filter(owner=request.user)
    else:
        sk = request.session.session_key
        cart_items = cartOrder.objects.filter(session_key=sk)
    subtotal = sum(item.price * item.quantity for item in cart_items) if cart_items else 0
    taxes = subtotal * Decimal('0.15') if subtotal else Decimal('0')
    total = subtotal + taxes if subtotal else Decimal('0')
    total_items = sum(item.quantity for item in cart_items)

    return JsonResponse({
        'success': True,
        'deleted_count': deleted_count,
        'subtotal': f"{subtotal:.2f}",
        'taxes': f"{taxes:.2f}",
        'total': f"{total:.2f}",
        'total_items': total_items,
    })


@require_POST
def add_to_cart(request):
    product_id = request.POST.get('product_id')
    if not product_id:
        return JsonResponse({'success': False, 'message': 'No product ID provided.'})

    try:
        product = Product.objects.get(pk=product_id)
    except Product.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Product not found.'})

    Cart.objects.create(product=product)
    total_items = Cart.objects.count()

    return JsonResponse({
        'success': True,
        'message': 'Item added to cart.',
        'cart_count': total_items
    })


# ---------------- SAMPLE PRODUCTS ---------------- #

def product_list_sample(request):
    all_products = list(Product.objects.all())
    random_products = sample(all_products, min(len(all_products), 6))
    return render(request, 'home.html', {'products': random_products})


def product_list(request):
    products = Product.objects.all()
    return render(request, 'home.html', {'products': products})


# ---------------- HOME VIEW (FIXED PAGINATION + SEARCH) ---------------- #


def product_create_view(request):
    if request.method == "POST":
        form = ProductForm(request.POST)
        if form.is_valid():
            location = form.cleaned_data["location"]
            # do something with location
    else:
        form = ProductForm()

    return render(request, "home.html", {"form": form})


def home(request):
    search_query = request.GET.get('search', '')
    filter_query = request.GET.get('filter', '')

    product_list = Product.objects.all().order_by('-id')

    if filter_query and filter_query.lower() != "all":
        product_list = product_list.filter(category__icontains=filter_query)

    if search_query:
        product_list = product_list.filter(
            Q(name__icontains=search_query) |
            Q(brand_model__icontains=search_query) |
            Q(optional_details__icontains=search_query) |
            Q(category__icontains=search_query) |
            Q(color__icontains=search_query)
        )

    paginator = Paginator(product_list, 6)
    page_number = request.GET.get("page")
    products = paginator.get_page(page_number)

    # Local helper: determine if a product field is meaningful (matches template filter logic)
    def is_meaningful(value):
        if value is None:
            return False
        try:
            s = str(value).strip()
        except Exception:
            return False
        if s == '':
            return False
        low = s.lower()
        na_variants = {'na', 'n/a', 'none', 'null', '-', 'n.a.', 'n.a', 'n/a.', 'n a', 'n.a..', 'unknown', 'n/a (not applicable)', 'n/a (na)'}
        if low in na_variants:
            return False
        return True

    # Annotate each product in the page with cleaned values so the template can display them
    try:
        for p in products:
            # list of fields we want to ensure are empty when not meaningful
            for field in ['brand_model', 'brand', 'color', 'storage_ram', 'network', 'battery', 'camera', 'screen', 'processor', 'os', 'accessories', 'condition', 'warranty', 'location', 'optional_details', 'description']:
                val = getattr(p, field, None)
                if is_meaningful(val):
                    # normalize whitespace
                    cleaned = str(val).strip()
                    # overwrite attribute on instance so template sees cleaned value
                    try:
                        setattr(p, field, cleaned)
                    except Exception:
                        pass
                else:
                    try:
                        setattr(p, field, '')
                    except Exception:
                        pass
    except TypeError:
        # products may not be iterable in some edge cases; ignore safely
        pass

    # Cart totals - scope to current user or session
    session_key = None
    try:
        session_key = request.session.session_key
    except Exception:
        session_key = None

    if request.user and request.user.is_authenticated:
        cart_qs = cartOrder.objects.filter(owner=request.user)
    else:
        if not session_key:
            try:
                request.session.create()
                session_key = request.session.session_key
            except Exception:
                session_key = None
        cart_qs = cartOrder.objects.filter(session_key=session_key) if session_key else cartOrder.objects.none()

    cartProducts = cart_qs.annotate(
        total_price=ExpressionWrapper(F('price') * F('quantity'), output_field=DecimalField())
    )
    subtotal = sum(item.price * item.quantity for item in cartProducts)
    taxes = subtotal * Decimal('0.15')
    total = subtotal + taxes

    # Orders - scope to current user or session
    if request.user and request.user.is_authenticated:
        orders = Order.objects.filter(owner=request.user).order_by('-date')
    else:
        orders = Order.objects.filter(session_key=session_key).order_by('-date') if session_key else Order.objects.none()
    # Try to attach a product_id attribute to orders when possible.
    # We avoid changing the DB schema now; instead, perform a best-effort lookup
    # by matching the order.product string to an existing Product name.
    try:
        for o in orders:
            o.product_id = None
            try:
                # First try exact match
                prod = Product.objects.filter(name__iexact=o.product).first()
                if not prod:
                    # Fallback: partial match on name or brand_model
                    prod = Product.objects.filter(Q(name__icontains=o.product) | Q(brand_model__icontains=o.product)).first()
                if prod:
                    o.product_id = prod.id
            except Exception:
                # If anything goes wrong, leave product_id as None
                o.product_id = None
    except Exception:
        # If orders is not iterable for some reason, ignore and continue
        pass
    total_price = sum(order.total for order in orders)
    today_date = timezone.now().strftime("%B %d, %Y")

    context = {
        'products': products,
        'date': datetime.now().strftime("%B %d, %Y"),
        'current_search': search_query,
        'current_filter': filter_query,

        'cartProducts': cartProducts,
        'cart_items': cartProducts,
        'subtotal': "%.2f" % subtotal,
        'taxes': "%.2f" % taxes,
        'total': "%.2f" % total,

        'orders': orders,
        'total_price': total_price,
        'today_date': today_date,
    }

    # Add bundles to context
    bundles = Bundle.objects.all().order_by('-created_at')[:6]
    context['bundles'] = bundles

    # Optional: allow opening a product detail inline on the home page
    # Optional: allow opening a product detail inline on the home page.
    # We support a one-time session-based trigger so the product container
    # is shown only once (prevents it from appearing on refresh).
    product_view_session_id = request.session.pop('product_view_once', None)
    if product_view_session_id:
        try:
            pv = Product.objects.get(pk=product_view_session_id)
            related_products = Product.objects.filter(category=pv.category).exclude(id=pv.id)[:4]
            context['product'] = pv
            context['related_products'] = related_products
            context['show_product_container'] = True
        except Product.DoesNotExist:
            pass

    else:
        # Fallback: support explicit query param (legacy)
        product_view_id = request.GET.get('product_view')
        if product_view_id:
            try:
                pv = Product.objects.get(pk=product_view_id)
                related_products = Product.objects.filter(category=pv.category).exclude(id=pv.id)[:4]
                context['product'] = pv
                context['related_products'] = related_products
                context['show_product_container'] = True
            except Product.DoesNotExist:
                pass

    # If a single product is being shown (product detail inline), ensure its fields are cleaned too
    if context.get('product'):
        p = context['product']
        def _is_meaningful_local(v):
            try:
                s = str(v).strip()
            except Exception:
                return False
            if s == '':
                return False
            return s.lower() not in {'na', 'n/a', 'none', 'null', '-', 'unknown'}

        for field in ['brand_model', 'brand', 'color', 'storage_ram', 'network', 'battery', 'camera', 'screen', 'processor', 'os', 'accessories', 'condition', 'warranty', 'location', 'optional_details', 'description']:
            val = getattr(p, field, None)
            if _is_meaningful_local(val):
                try:
                    setattr(p, field, str(val).strip())
                except Exception:
                    pass
            else:
                try:
                    setattr(p, field, '')
                except Exception:
                    pass

    return render(request, 'website/home.html', context)


# ---------------- CART QUANTITY UPDATE ---------------- #

@require_POST
def update_cart_quantity(request):
    product_id = request.POST.get('product_id')
    quantity = int(request.POST.get('quantity', 1))
    
    try:
        # Scope lookup by user or session
        session_key = None
        try:
            session_key = request.session.session_key
        except Exception:
            session_key = None

        if request.user and request.user.is_authenticated:
            cart_item = cartOrder.objects.get(product_id=product_id, owner=request.user)
        else:
            if not session_key:
                try:
                    request.session.create()
                    session_key = request.session.session_key
                except Exception:
                    session_key = None
            cart_item = cartOrder.objects.get(product_id=product_id, session_key=session_key)

        cart_item.quantity = quantity
        cart_item.save()

        # Recompute scoped totals
        if request.user and request.user.is_authenticated:
            cart_items = cartOrder.objects.filter(owner=request.user)
        else:
            cart_items = cartOrder.objects.filter(session_key=session_key) if session_key else cartOrder.objects.none()

        subtotal = sum(item.price * item.quantity for item in cart_items)
        taxes = subtotal * Decimal('0.15')
        total = subtotal + taxes

        return JsonResponse({
            'success': True,
            'subtotal': "%.2f" % subtotal,
            'taxes': "%.2f" % taxes,
            'total': "%.2f" % total,
            'item_total': "%.2f" % (cart_item.price * cart_item.quantity),
        })
    except cartOrder.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Item not found'})


# ---------------- API ENDPOINTS ---------------- #

@api_view(['GET'])
def live_search_products(request):
    query = request.GET.get('search', '')
    products = Product.objects.all()
    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(brand_model__icontains=query) |
            Q(optional_details__icontains=query) |
            Q(category__icontains=query) |
            Q(color__icontains=query)
        )
    serializer = ProductSerializer(products, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['GET', 'POST'])
def bundles_list_create(request):
    if request.method == 'GET':
        bundles = Bundle.objects.all().order_by('-created_at')
        serializer = BundleSerializer(bundles, many=True, context={'request': request})
        return Response(serializer.data)
    else:
        # Accept both JSON and multipart/form-data where 'products' may be provided as
        # a JSON list in a 'products' field or as repeated form fields. Normalize it first.
        data = request.data.copy()
        # If products provided as JSON string in form-data, try to parse
        prods = data.get('products')
        if prods and isinstance(prods, str):
            try:
                parsed = json.loads(prods)
                data.setlist('products', [str(p) for p in parsed])
            except Exception:
                # leave as-is and let serializer validate
                pass

        # Quick validation: if 'products' is list-like and >2, return friendly error
        try:
            prods_list = data.getlist('products') if hasattr(data, 'getlist') else data.get('products')
            if prods_list and isinstance(prods_list, (list, tuple)) and len(prods_list) > 2:
                return Response({'products': ['A bundle can contain at most 2 products.']}, status=400)
        except Exception:
            pass

        serializer = BundleSerializer(data=data)
        if serializer.is_valid():
            # Save with an enhanced retry loop to handle transient sqlite locking errors.
            # Use exponential backoff and ensure the DB connection is closed/rolled back
            # between attempts to clear any leftover locks.
            max_attempts = 8
            attempt = 0
            bundle = None
            from django.db import DatabaseError, connection, transaction
            import time
            while attempt < max_attempts:
                try:
                    # Use atomic to ensure partial writes are not left open
                    with transaction.atomic():
                        bundle = serializer.save()
                    break
                except DatabaseError as e:
                    msg = str(e).lower()
                    if 'locked' in msg or 'database is locked' in msg:
                        attempt += 1
                        # exponential backoff: 0.1, 0.2, 0.4, ... capped at ~2s
                        sleep_time = min(0.1 * (2 ** (attempt - 1)), 2.0)
                        try:
                            time.sleep(sleep_time)
                        except Exception:
                            pass
                        # ensure connection is clean for next try
                        try:
                            if connection.in_atomic_block:
                                # rollback any open transaction
                                transaction.set_rollback(True)
                        except Exception:
                            pass
                        try:
                            connection.close()
                        except Exception:
                            pass
                        continue
                    # re-raise for other DB errors
                    raise
            if bundle is None:
                return Response({'detail': 'Database is locked, please try again.'}, status=503)
            # If products included, ensure M2M relationship is set
            if 'products' in serializer.validated_data:
                bundle.products.set(serializer.validated_data.get('products', []))
            return Response(BundleSerializer(bundle, context={'request': request}).data, status=201)
        return Response(serializer.errors, status=400)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
def bundle_detail(request, pk):
    try:
        bundle = Bundle.objects.get(pk=pk)
    except Bundle.DoesNotExist:
        return Response({'detail': 'Not found'}, status=404)

    if request.method == 'GET':
        serializer = BundleSerializer(bundle, context={'request': request})
        return Response(serializer.data)
    if request.method in ['PUT', 'PATCH']:
        data = request.data.copy()
        prods = data.get('products')
        if prods and isinstance(prods, str):
            try:
                parsed = json.loads(prods)
                data.setlist('products', [str(p) for p in parsed])
            except Exception:
                pass

        try:
            prods_list = data.getlist('products') if hasattr(data, 'getlist') else data.get('products')
            if prods_list and isinstance(prods_list, (list, tuple)) and len(prods_list) > 2:
                return Response({'products': ['A bundle can contain at most 2 products.']}, status=400)
        except Exception:
            pass

        serializer = BundleSerializer(bundle, data=data, partial=(request.method == 'PATCH'))
        if serializer.is_valid():
            bundle = serializer.save()
            # Update M2M after save
            if 'products' in serializer.validated_data:
                bundle.products.set(serializer.validated_data.get('products', []))
            return Response(BundleSerializer(bundle, context={'request': request}).data)
        return Response(serializer.errors, status=400)
    if request.method == 'DELETE':
        bundle.delete()
        return Response(status=204)


@api_view(['GET'])
def get_orders(request):
    # Scope orders to authenticated user or session
    session_key = None
    try:
        session_key = request.session.session_key
    except Exception:
        session_key = None

    if request.user and request.user.is_authenticated:
        orders = Order.objects.filter(owner=request.user).order_by('-date')
    else:
        orders = Order.objects.filter(session_key=session_key).order_by('-date') if session_key else Order.objects.none()
    serializer = OrderSerializer(orders, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['PATCH'])
def update_order_status(request, pk):
    """Patch endpoint to update an order's delivery_status.

    Accepts JSON body: { "delivery_status": "pending|shipped|delivered" }
    """
    # Ensure the order belongs to the requesting user/session
    session_key = None
    try:
        session_key = request.session.session_key
    except Exception:
        session_key = None

    try:
        if request.user and request.user.is_authenticated:
            order = Order.objects.get(pk=pk, owner=request.user)
        else:
            order = Order.objects.get(pk=pk, session_key=session_key)
    except Order.DoesNotExist:
        return Response({'detail': 'Not found'}, status=404)

    try:
        data = request.data if isinstance(request.data, dict) else json.loads(request.body)
    except Exception:
        return Response({'detail': 'Invalid request body'}, status=400)

    status_val = data.get('delivery_status')
    if not status_val:
        return Response({'detail': 'delivery_status is required'}, status=400)

    # Validate value against model choices
    allowed = [c[0] for c in Order.DELIVERY_STATUS_CHOICES]
    if status_val not in allowed:
        return Response({'detail': 'Invalid delivery_status value'}, status=400)
# Persist the new status, notify websocket clients (best-effort), and return the serialized order.
    order.delivery_status = status_val
    try:
        order.save()
        serializer = OrderSerializer(order, context={'request': request})

        # Best-effort broadcast to websocket group 'site_updates'
        try:
            from asgiref.sync import async_to_sync
            from channels.layers import get_channel_layer

            channel_layer = get_channel_layer()
            if channel_layer is not None:
                async_to_sync(channel_layer.group_send)(
                    'site_updates',
                    {
                        'type': 'site_update',
                        'data': {
                            'order_id': order.id,
                            'delivery_status': order.delivery_status,
                        }
                    }
                )
        except Exception:
            # Non-fatal: continue even if broadcast fails
            pass

        return Response(serializer.data)
    except Exception as e:
        return Response({'detail': str(e)}, status=500)


# Helpful human-readable HTTP endpoint for the websocket path.
# This avoids a 404 when someone visits /ws/updates/ in a browser and
# provides a brief explanation that this is a WebSocket endpoint.
def ws_updates_view(request):
    from django.http import HttpResponse

    content = (
        '<html><body><h2>WebSocket endpoint</h2>'
        '<p>This URL is reserved for WebSocket connections (updates stream).</p>'
        '<p>Use a WebSocket client to connect to <code>/ws/updates/</code>.</p>'
        '</body></html>'
    )
    return HttpResponse(content)



@api_view(['POST'])
def remove_order(request):
    """Remove an order by ID. Expects JSON body: {"id": <order_id>}"""
    try:
        data = request.data if isinstance(request.data, dict) else json.loads(request.body)
    except Exception:
        return JsonResponse({'success': False, 'message': 'Invalid request body'}, status=400)

    order_id = data.get('id')
    if not order_id:
        return JsonResponse({'success': False, 'message': 'Missing order id'}, status=400)

    # Ensure the order belongs to the current user/session before deleting
    session_key = None
    try:
        session_key = request.session.session_key
    except Exception:
        session_key = None

    try:
        if request.user and request.user.is_authenticated:
            order = Order.objects.get(pk=order_id, owner=request.user)
        else:
            order = Order.objects.get(pk=order_id, session_key=session_key)
    except Order.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Order not found'}, status=404)

    try:
        order.delete()
        return JsonResponse({'success': True, 'message': 'Order removed'})
    except Exception:
        return JsonResponse({'success': False, 'message': 'Failed to remove order'}, status=500)


@api_view(['GET'])
def get_products(request):
    products = Product.objects.all().order_by('-id')
    paginator = PageNumberPagination()
    paginator.page_size = 6
    result_page = paginator.paginate_queryset(products, request)
    serializer = ProductSerializer(result_page, many=True, context={'request': request})
    return paginator.get_paginated_response(serializer.data)


@api_view(['DELETE'])
def delete_product(request, pk):
    try:
        product = Product.objects.get(pk=pk)
        product.delete()
        return Response(status=204)
    except Product.DoesNotExist:
        return Response(status=404)


# ---------------- PRODUCT DASHBOARD ---------------- #

def product_dashboard(request):
    product_list = Product.objects.all()
    paginator = Paginator(product_list, 6)
    page_number = request.GET.get("page")
    products = paginator.get_page(page_number)
    return render(request, "your_template.html", {"products": products})


# ---------------- CREATE PRODUCT ---------------- #

class ProductCreateView(APIView):
    parser_classes = (MultiPartParser, FormParser)
    def post(self, request, format=None):
        serializer = ProductSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            product = serializer.save()
            # Return serialized product with request context so ImageFields become absolute URLs
            return Response(ProductSerializer(product, context={'request': request}).data, status=201)
        return Response(serializer.errors, status=400)


# ---------------- PLACE ORDER ---------------- #

@csrf_exempt
@api_view(['POST'])
def place_order(request):
    try:
        data = json.loads(request.body)
        first_name = data.get('firstName')
        last_name = data.get('lastName')
        phone_number = data.get('phoneNumber')
        location = data.get('location')
        cart_items = data.get('cartItems', [])

        if not all([first_name, last_name, phone_number, location]):
            return JsonResponse({'error': 'Missing customer details'}, status=400)
        if not cart_items:
            return JsonResponse({'error': 'Cart is empty'}, status=400)

        for item in cart_items:
            quantity = item.get('qty')
            price = item.get('price')
            product_name = item.get('name')
            if not all([quantity, price, product_name]):
                continue

            total = quantity * price
            # Attach owner or session_key to the order for scoping
            order_kwargs = {
                'first_name': first_name,
                'last_name': last_name,
                'phone_number': phone_number,
                'location': location,
                'product': product_name,
                'quantity': quantity,
                'price': price,
                'total': total,
            }
            try:
                if request.user and request.user.is_authenticated:
                    order_kwargs['owner'] = request.user
                else:
                    if not request.session.session_key:
                        request.session.save()
                    order_kwargs['session_key'] = request.session.session_key
            except Exception:
                pass

            Order.objects.create(**order_kwargs)

        return JsonResponse({'status': 'success'}, status=200)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ---------------- ADD TO CART ---------------- #
from decimal import Decimal
from django.http import JsonResponse
from django.utils import timezone
from .models import cartOrder, Product  # ✅ Make sure these imports exist
from urllib.parse import urlparse
from django.conf import settings

def addProduct_to_cart(request):
    if request.method == "POST":
        # DEV: when debugging locally, log incoming POST keys/values to help
        # diagnose missing-field issues. Only active when DEBUG=True.
        if getattr(settings, 'DEBUG', False):
            try:
                safe_post = {k: ('<redacted>' if k.lower() == 'csrfmiddlewaretoken' else v) for k, v in request.POST.items()}
                logger.info("addProduct_to_cart received POST data: %s", safe_post)
            except Exception:
                logger.exception("Failed to log POST data in addProduct_to_cart")
        product_id = request.POST.get("product_id")
        name = request.POST.get("name")
        price = request.POST.get("price")
        condition = request.POST.get("condition")
        category = request.POST.get("category")
        image_url = request.POST.get("image_url")

        # Normalize image path before storing:
        # - Accept absolute URLs (http/https) or relative paths (/media/... or media/...) or static paths
        # - Store media-relative path like 'products/xxx.jpg' for ImageField compatibility
        stored_image = ''
        try:
            if image_url:
                img = image_url.strip()
                # If absolute URL, extract path portion
                if img.startswith('http://') or img.startswith('https://'):
                    parsed = urlparse(img)
                    img_path = parsed.path or ''
                else:
                    img_path = img
                # Remove leading slashes
                while img_path.startswith('/'):
                    img_path = img_path[1:]
                # If image path begins with MEDIA_URL (like 'media/products/...'), strip the leading 'media/'
                media_prefix = settings.MEDIA_URL.lstrip('/') if getattr(settings, 'MEDIA_URL', '').startswith('/') else settings.MEDIA_URL
                if media_prefix and img_path.startswith(media_prefix):
                    img_path = img_path[len(media_prefix):]
                # If the resulting path points to static assets, leave stored_image empty so default handling applies
                if img_path.startswith('static/') or img_path.startswith('website/'):
                    stored_image = ''
                else:
                    stored_image = img_path
        except Exception:
            stored_image = ''

        if not product_id or not name or not price:
            return JsonResponse({'success': False, 'message': 'Missing required fields.'}, status=400)

        try:
            price_decimal = Decimal(price)
            pid_int = int(product_id)

            # Ensure product exists and is available before adding to cart
            prod = Product.objects.filter(pk=pid_int).first()
            if not prod:
                return JsonResponse({'success': False, 'message': 'Product not found.'}, status=404)
            if not getattr(prod, 'available', True):
                return JsonResponse({'success': False, 'message': 'Product is out of stock.'}, status=400)

            # If the same product already exists in this visitor's cart, increment quantity
            if request.user.is_authenticated:
                existing = cartOrder.objects.filter(product_id=pid_int, owner=request.user).first()
            else:
                if not request.session.session_key:
                    request.session.save()
                existing = cartOrder.objects.filter(product_id=pid_int, session_key=request.session.session_key).first()

            if existing:
                existing.quantity = (existing.quantity or 0) + 1
                # update price if needed (keep existing price otherwise)
                try:
                    existing.price = price_decimal
                except Exception:
                    pass
                existing.save()
                # compute scoped total
                if request.user.is_authenticated:
                    total_items = sum(item.quantity for item in cartOrder.objects.filter(owner=request.user))
                else:
                    total_items = sum(item.quantity for item in cartOrder.objects.filter(session_key=request.session.session_key))
                return JsonResponse({'success': True, 'message': 'Product Successfully updated in cart.', 'product_id': pid_int, 'quantity': existing.quantity, 'cart_count': total_items})

            # Create new cart item if not existing. Attach owner or session_key for scoping.
            kwargs = dict(
                product_id=pid_int,
                name=name,
                price=price_decimal,
                condition=condition if condition else "N/A",
                category=category if category else "Uncategorized",
                image=stored_image,
                added_at=timezone.now(),
                quantity=1
            )
            if request.user.is_authenticated:
                kwargs['owner'] = request.user
            else:
                if not request.session.session_key:
                    request.session.save()
                kwargs['session_key'] = request.session.session_key

            cartOrder.objects.create(**kwargs)
            if request.user.is_authenticated:
                total_items = sum(item.quantity for item in cartOrder.objects.filter(owner=request.user))
            else:
                total_items = sum(item.quantity for item in cartOrder.objects.filter(session_key=request.session.session_key))
            return JsonResponse({'success': True, 'message': 'Product added to cart.', 'product_id': pid_int, 'quantity': 1, 'cart_count': total_items})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Error: {str(e)}'}, status=500)

    return JsonResponse({'success': False, 'message': 'Only POST requests are allowed.'}, status=405)

# ---------------- CART API ---------------- #

def cart_api(request):
    # Scope cart items to current user or session
    if request.user.is_authenticated:
        cart_items_qs = cartOrder.objects.filter(owner=request.user)
    else:
        if not request.session.session_key:
            request.session.save()
        cart_items_qs = cartOrder.objects.filter(session_key=request.session.session_key)

    cart_items = cart_items_qs.annotate(
        total_price=ExpressionWrapper(F('price') * F('quantity'), output_field=DecimalField())
    )
    subtotal = Decimal('0')
    items_list = []
    for item in cart_items:
        # Build an absolute URL for the image when possible so front-end can use it directly
        img_url = ''
        try:
            if item.image:
                if item.image.startswith('http://') or item.image.startswith('https://'):
                    img_url = item.image
                else:
                    # item.image is stored as a media-relative path like 'products/123.jpg'
                    media_prefix = settings.MEDIA_URL if getattr(settings, 'MEDIA_URL', '/') else '/media/'
                    img_url = request.build_absolute_uri('/' + media_prefix.lstrip('/') + item.image.lstrip('/'))
        except Exception:
            img_url = item.image or ''

        items_list.append({
            'product_id': item.product_id,
            'name': item.name,
            'quantity': item.quantity,
            'price': float(item.price),
            'total_price': float(item.total_price),
            'image': img_url,
            'condition': item.condition or '',
            'category': item.category or '',
        })
        subtotal += item.price * item.quantity
        
    subtotal = subtotal / Decimal(1.15)
    taxes = subtotal * Decimal(0.15)
    total = subtotal + taxes

    return JsonResponse({
        'cart_items': items_list,
        'subtotal': f"{subtotal:.2f}",
        'taxes': f"{taxes:.2f}",
        'total': f"{total:.2f}",
        'total_items': sum(item['quantity'] for item in items_list),
    })


# ---------------- CHECKOUT ---------------- #

def checkout(request):
    # Scope cart items to current user or session
    if request.user.is_authenticated:
        cart_items = cartOrder.objects.filter(owner=request.user)
    else:
        if not request.session.session_key:
            request.session.save()
        cart_items = cartOrder.objects.filter(session_key=request.session.session_key)
    subtotal = sum(item.price * item.quantity for item in cart_items)

    # Default values
    delivery_cost = 0
    total = subtotal

    if request.method == "POST":
        full_name = request.POST.get("fullname", "")
        first_name, last_name = (full_name.strip().split(" ", 1) + [""])[:2]
        phone = request.POST.get("phone", "")
        delivery_location = request.POST.get("delivery_location")
        address = request.POST.get("address", "")
        notes = request.POST.get("notes", "")

        # Determine delivery cost based on location
        if delivery_location.lower() == "harare":
            delivery_cost = 5
        elif delivery_location.lower() == "harare suburbs":
            delivery_cost = 7
        elif delivery_location.lower() == "bulawayo":
            delivery_cost = 6
        elif delivery_location.lower() == "bulawayo suburbs":
            delivery_cost = 8
        elif delivery_location.lower() == "mutare":
            delivery_cost = 7
        elif delivery_location.lower() == "mutare suburbs":
            delivery_cost = 9
        elif delivery_location.lower() == "gweru":
            delivery_cost = 6
        elif delivery_location.lower() == "masvingo":
            delivery_cost = 7
        elif delivery_location.lower() == "masvingo town":
            delivery_cost = 8
        elif delivery_location.lower() == "kadoma":
            delivery_cost = 6
        elif delivery_location.lower() == "kwekwe":
            delivery_cost = 6
        elif delivery_location.lower() == "marondera":
            delivery_cost = 5
        elif delivery_location.lower() == "chegutu":
            delivery_cost = 5
        elif delivery_location.lower() == "bindura":
            delivery_cost = 6
        elif delivery_location.lower() == "chipinge":
            delivery_cost = 7
        elif delivery_location.lower() == "chinhoyi":
            delivery_cost = 5
        elif delivery_location.lower() == "mutoko":
            delivery_cost = 6
        elif delivery_location.lower() == "ruwa":
            delivery_cost = 5
        elif delivery_location.lower() == "checheche":
            delivery_cost = 5
        elif delivery_location.lower() == "shurugwi":
            delivery_cost = 6
        elif delivery_location.lower() == "redcliff":
            delivery_cost = 5
        elif delivery_location.lower() == "gokwe":
            delivery_cost = 8
        elif delivery_location.lower() == "beitbridge":
            delivery_cost = 10
        elif delivery_location.lower() == "chisumbanje":
            delivery_cost = 9
        elif delivery_location.lower() == "murewa":
            delivery_cost = 6
        elif delivery_location.lower() == "maramba":
            delivery_cost = 7
        elif delivery_location.lower() == "esigodini":
            delivery_cost = 6
        elif delivery_location.lower() == "zvishavane":
            delivery_cost = 8
        else:
            delivery_cost = 0  # default if location not recognized

        # Add delivery cost to total
        total = subtotal + delivery_cost

        # Create orders
        for item in cart_items:
            # Normalize cart item image into a media-relative path for Order.image
            ord_img = ''
            try:
                img = (item.image or '').strip()
                if img.startswith('http://') or img.startswith('https://'):
                    # extract path and strip leading '/media/' if present
                    parsed = urlparse(img)
                    p = parsed.path or ''
                else:
                    p = img
                while p.startswith('/'):
                    p = p[1:]
                media_prefix = settings.MEDIA_URL.lstrip('/') if getattr(settings, 'MEDIA_URL', '').startswith('/') else settings.MEDIA_URL
                if media_prefix and p.startswith(media_prefix):
                    p = p[len(media_prefix):]
                # ensure we only store non-static media paths
                if p and not p.startswith('static/') and not p.startswith('website/'):
                    ord_img = p
            except Exception:
                ord_img = ''

            order_kwargs = {
                'first_name': first_name,
                'last_name': last_name,
                'phone_number': phone,
                'location': address,
                'delivery_notes': notes,
                'product': item.name,
                'quantity': item.quantity,
                'price': item.price,
                'total': item.price * item.quantity,
                'image': ord_img,
                'delivery_cost': delivery_cost
            }
            try:
                if request.user and request.user.is_authenticated:
                    order_kwargs['owner'] = request.user
                else:
                    if not request.session.session_key:
                        request.session.save()
                    order_kwargs['session_key'] = request.session.session_key
            except Exception:
                pass

            Order.objects.create(**order_kwargs)
        # Clear cart for current user/session only
        if request.user and request.user.is_authenticated:
            cartOrder.objects.filter(owner=request.user).delete()
        else:
            if request.session.session_key:
                cartOrder.objects.filter(session_key=request.session.session_key).delete()
            else:
                # nothing to delete if session unknown
                pass
        return redirect("home")

    # GET request: show checkout page
    return render(request, 'home.html', {
        'cart_items': cart_items,
        'subtotal': subtotal,
        'delivery_cost': delivery_cost,
        'total': total
    })

from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from .models import Product

def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    related_products = Product.objects.filter(category=product.category).exclude(id=product.id)[:4]

    # Call the home view to get its response
    home_response = home(request)
    
    # The context is in the 'context_data' attribute of the response if it's a TemplateResponse,
    # but render() returns an HttpResponse. We need to rebuild the context.
    # A better long-term solution is to refactor context creation into a helper function.
    # For now, let's just get the context from the home view's response if possible, or rebuild it.
    
    # Let's rebuild the context needed from home()
    search_query = request.GET.get('search', '')
    filter_query = request.GET.get('filter', '')

    product_list = Product.objects.all().order_by('-id')

    if filter_query and filter_query.lower() != "all":
        product_list = product_list.filter(category__icontains=filter_query)

    if search_query:
        product_list = product_list.filter(
            Q(name__icontains=search_query) |
            Q(brand_model__icontains=search_query) |
            Q(optional_details__icontains=search_query) |
            Q(category__icontains=search_query) |
            Q(color__icontains=search_query)
        )

    paginator = Paginator(product_list, 6)
    page_number = request.GET.get("page")
    products = paginator.get_page(page_number)

    # Cart totals - scope to current user/session
    session_key = None
    try:
        session_key = request.session.session_key
    except Exception:
        session_key = None

    if request.user and request.user.is_authenticated:
        cart_qs = cartOrder.objects.filter(owner=request.user)
    else:
        if not session_key:
            try:
                request.session.create()
                session_key = request.session.session_key
            except Exception:
                session_key = None
        cart_qs = cartOrder.objects.filter(session_key=session_key) if session_key else cartOrder.objects.none()

    cartProducts = cart_qs.annotate(
        total_price=ExpressionWrapper(F('price') * F('quantity'), output_field=DecimalField())
    )
    subtotal = sum(item.price * item.quantity for item in cartProducts)
    taxes = subtotal * Decimal('0.15')
    total = subtotal + taxes

    # Orders - scope to current user/session
    if request.user and request.user.is_authenticated:
        orders = Order.objects.filter(owner=request.user).order_by('-date')
    else:
        orders = Order.objects.filter(session_key=session_key).order_by('-date') if session_key else Order.objects.none()
    total_price = sum(order.total for order in orders)
    today_date = timezone.now().strftime("%B %d, %Y")

    context = {
        'products': products,
        'date': datetime.now().strftime("%B %d, %Y"),
        'current_search': search_query,
        'current_filter': filter_query,

        'cartProducts': cartProducts,
        'cart_items': cartProducts,
        'subtotal': "%.2f" % subtotal,
        'taxes': "%.2f" % taxes,
        'total': "%.2f" % total,

        'orders': orders,
        'total_price': total_price,
        'today_date': today_date,
    }
    
    # Add product-specific details to the context
    context['product'] = product
    context['related_products'] = related_products
    context['show_product_container'] = True # Flag to display the product detail section

    return render(request, 'website/home.html', context)

@api_view(['GET'])
def get_product_detail(request, pk):
    try:
        product = Product.objects.get(pk=pk)
    except Product.DoesNotExist:
        return Response({'detail': 'Not found'}, status=404)

    related = Product.objects.filter(category=product.category).exclude(id=product.id)[:4]
    product_data = ProductSerializer(product, context={'request': request}).data
    related_data = ProductSerializer(related, many=True, context={'request': request}).data
    return Response({'product': product_data, 'related': related_data})
