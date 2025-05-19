from django.db.models import Sum
from rest_framework import serializers

from shop.models import Basket
from shop.serializers import ShopSerializer
from .models import ProductImage, ProductVariant, Product, ProductVolume, ProductSize, ProductTaste, ProductColor, \
    ProductCategory


class ProductCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductCategory
        fields = ["id", "name", "image"]


class ProductColorSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductColor
        fields = '__all__'


class ProductSizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductSize
        fields = '__all__'


class ProductTasteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductTaste
        fields = '__all__'


class ProductVolumeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVolume
        fields = '__all__'


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image']

class ProductVariantSerializer(serializers.ModelSerializer):
    color = serializers.StringRelatedField()
    size = serializers.StringRelatedField()
    volume = serializers.StringRelatedField()
    taste = serializers.StringRelatedField()
    quantity = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()
    product_name = serializers.SerializerMethodField()

    def get_product_name(self, obj):
        return obj.product.product_name if obj.product else None

    def get_images(self, obj):
        images = obj.product.images.all()  # assuming a reverse relation: `related_name='images'` in ProductImage
        return [image.image.url for image in images]

    def get_quantity(self, obj):
        request = self.context.get("request")
        if request:
            telegram_id = request.query_params.get("telegram_id")
            try:
                basket = Basket.objects.get(user__telegram_id=telegram_id, product_variant=obj)
                return basket.quantity
            except Basket.DoesNotExist:
                return 0
        return None

    class Meta:
        model = ProductVariant
        fields = [
            'id', 'color', 'size', 'volume', 'taste',
            'price', 'discount_price', 'discount_percent', 'prepayment_amount',
            'stock', 'is_active', 'images', 'quantity', 'product_name'
        ]



class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True)
    variants = ProductVariantSerializer(many=True)

    class Meta:
        model = Product
        fields = [
            'id', 'shop', 'category', 'product_name_uz', 'product_name_ru',
            'description_uz', 'description_ru', 'created_at', 'updated_at',
            'images', 'variants'
        ]

    def create(self, validated_data):
        images_data = validated_data.pop('images', [])
        variants_data = validated_data.data.pop('variants', [])
        product = Product.objects.create(**validated_data)

        for image_data in images_data:
            ProductImage.objects.create(product=product, **image_data)
        for variants_data in variants_data:
            ProductVariant.objects.create(product=product, **variants_data)
        return product


class ProductGetSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True)
    variants = ProductVariantSerializer(many=True)
    category = ProductCategorySerializer()
    shop = ShopSerializer()

    quantity = serializers.SerializerMethodField()

    def get_quantity(self, obj):
        request = self.context.get("request")
        if request:
            telegram_id = request.query_params.get("telegram_id")
            if telegram_id:
                variants = obj.variants.all()
                total_quantity = Basket.objects.filter(
                    user__telegram_id=telegram_id,
                    product_variant__in=variants
                ).aggregate(total=Sum('quantity'))['total'] or 0

        return 0

    class Meta:
        model = Product
        fields = [
            'id', 'shop', 'category', 'product_name',
            'description', 'created_at', 'updated_at',
            'images', 'variants', 'quantity'
        ]
