from rest_framework import serializers
from .models import ProductImage, ProductVariant, Product


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image']


class ProductVariantSerializer(serializers.ModelSerializer):
    color = serializers.StringRelatedField()
    size = serializers.StringRelatedField()
    volume = serializers.StringRelatedField()
    taste = serializers.StringRelatedField()

    class Meta:
        model = ProductVariant
        fields = [
            'id', 'color', 'size', 'volume', 'taste',
            'price', 'discount_price', 'discount_percent', 'prepayment_amount',
            'stock', 'is_active'
        ]


class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)
    category = serializers.StringRelatedField()
    shop = serializers.StringRelatedField()

    class Meta:
        model = Product
        fields = [
            'id', 'shop', 'category', 'product_name',
            'description', 'created_at', 'updated_at',
            'images', 'variants'
        ]
