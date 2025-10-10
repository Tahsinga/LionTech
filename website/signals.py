from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Product, cartOrder, Order
import json

channel_layer = get_channel_layer()


def broadcast(action, instance, model_name):
    try:
        payload = {
            'action': action,
            'model': model_name,
            'data': {},
        }
        # include a compact set of fields helpful to the frontend
        if model_name == 'Product':
            payload['data'] = {'id': instance.id, 'name': instance.name, 'price': str(instance.price), 'available': bool(instance.available)}
        elif model_name == 'cartOrder':
            payload['data'] = {'product_id': instance.product_id, 'name': instance.name, 'quantity': instance.quantity, 'price': str(instance.price)}
        elif model_name == 'Order':
                payload['data'] = {
                    'order_id': instance.id,
                    'id': instance.id,
                    'order_number': getattr(instance, 'order_number', None),
                    'product': instance.product,
                    'quantity': instance.quantity,
                    'total': str(instance.total),
                    'delivery_status': getattr(instance, 'delivery_status', None),
                }

        async_to_sync(channel_layer.group_send)('site_updates', {'type': 'site_update', 'data': payload})
    except Exception:
        # avoid raising from signals
        pass


@receiver(post_save, sender=Product)
def product_saved(sender, instance, created, **kwargs):
    broadcast('created' if created else 'updated', instance, 'Product')


@receiver(post_delete, sender=Product)
def product_deleted(sender, instance, **kwargs):
    broadcast('deleted', instance, 'Product')


@receiver(post_save, sender=cartOrder)
def cartorder_saved(sender, instance, created, **kwargs):
    broadcast('created' if created else 'updated', instance, 'cartOrder')


@receiver(post_delete, sender=cartOrder)
def cartorder_deleted(sender, instance, **kwargs):
    broadcast('deleted', instance, 'cartOrder')


@receiver(post_save, sender=Order)
def order_saved(sender, instance, created, **kwargs):
    broadcast('created' if created else 'updated', instance, 'Order')


@receiver(post_delete, sender=Order)
def order_deleted(sender, instance, **kwargs):
    broadcast('deleted', instance, 'Order')
