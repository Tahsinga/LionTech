from django.urls import path
from . import views
# project/urls.py
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('ws/updates/', views.ws_updates_view, name='ws_updates'),
    path('place-order/', views.place_order, name='place_order'),
    path('api/orders/', views.get_orders),
    path('api/orders/<int:pk>/status/', views.update_order_status),
    path('', views.home, name='home'),

    # Separate GET and POST endpoints
    path('api/products/', views.get_products, name='get-products'),  # <- GET
    path('api/products/add/', views.ProductCreateView.as_view(), name='add-product'),  # <- POST
    path('api/bundles/', views.bundles_list_create, name='bundles_list_create'),
    path('api/bundles/<int:pk>/', views.bundle_detail, name='bundle_detail'),
    path('api/orders/', views.get_orders),
    path('api/products/create/', views.ProductCreateView.as_view(), name='create_product'), 

    path('api/products/<int:pk>/', views.delete_product),
    path('admin/', admin.site.urls),
    path('live-search-products/', views.live_search_products, name='live_search_products'),

    path('products/', views.product_list, name='product_list'),
    path('addProduct_to_cart/', views.addProduct_to_cart, name='addProduct_to_cart'),

    path('add-to-cart/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('update-cart-quantity/', views.update_cart_quantity, name='update_cart_quantity'),
    path('api/cart/', views.cart_api, name='cart_api'),

    path('checkout/', views.checkout, name='checkout'),
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
    path('api/product/<int:pk>/', views.get_product_detail, name='api_product_detail'),
    path('orders/remove/', views.remove_order, name='remove_order'),

    # Account management (simple email-as-username)
    path('accounts/register/', views.account_register, name='account_register'),
    path('accounts/login/', views.account_login, name='account_login'),
    path('accounts/logout/', views.account_logout, name='account_logout'),
    path('accounts/verify/<str:uidb64>/<str:token>/', views.account_verify, name='account_verify'),
    path('accounts/resend-verification/', views.account_resend_verification, name='account_resend_verification'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)



