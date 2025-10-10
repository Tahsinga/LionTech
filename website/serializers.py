from rest_framework import serializers
from .models import Product, Order
from .models import Bundle


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        # Explicitly list fields to include the new image slots
        fields = [
            'id', 'name', 'image', 'image_2', 'image_3', 'image_4', 'price', 'category', 'available',
            'brand_model', 'color', 'storage_ram', 'network', 'battery', 'camera', 'screen', 'processor',
            'os', 'accessories', 'condition', 'warranty', 'location', 'optional_details',
        ]


class OrderSerializer(serializers.ModelSerializer):
    customer = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'id',
            'first_name',
            'last_name',
            'phone_number',
            'location',
            'delivery_notes',
            'delivery_status',
            'product',
            'quantity',
            'price',
            'total',
            'date',
            'image',
            'order_number',
            'delivery_cost',
            'customer',
        ]

    def get_customer(self, obj):
        return f"{obj.first_name} {obj.last_name}"


class BundleSerializer(serializers.ModelSerializer):
    # Allow product ids to be included with a bundle
    products = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all(), many=True, required=False)
    # When returning data, also include product details
    product_details = ProductSerializer(source='products', many=True, read_only=True)

    def validate_products(self, value):
        # Ensure at most 2 products per bundle
        if value and len(value) > 2:
            raise serializers.ValidationError('A bundle can contain at most 2 products.')
        return value

    class Meta:
        model = Bundle
        fields = ['id', 'title', 'image', 'image_2', 'image_3', 'image_4', 'image_desc_1', 'image_desc_2', 'price', 'description', 'badge', 'created_at', 'products', 'product_details']
