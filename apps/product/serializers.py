from rest_framework import serializers
from botuser.models import FavoriteProduct
from shop.models import Basket
from .models import ProductImage, ProductVariant, Product, ProductVolume, ProductSize, ProductTaste, ProductColor, \
    ProductCategory


class ProductCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductCategory
        fields = ["id", "name", "image", "shop"]


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
        fields = ['id', 'image', 'product']


class ProductVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariant
        fields = [
            'color', 'size', 'volume', 'taste',
            'price', 'discount_price', 'discount_percent',
            'stock', 'is_active'
        ]


class ProductVariantPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariant
        fields = [
            'id', 'color', 'size', 'volume', 'taste', 'product',
            'price', 'discount_price', 'discount_percent',
            'stock', 'is_active'
        ]


class ProductVariantGetSerializer(serializers.ModelSerializer):
    color = ProductColorSerializer()
    size = ProductSizeSerializer()
    volume = ProductVolumeSerializer()
    taste = ProductTasteSerializer()
    images = serializers.SerializerMethodField()
    product_name = serializers.SerializerMethodField()

    def get_product_name(self, obj):
        return obj.product.product_name if obj.product else None

    def get_images(self, obj):
        images = obj.product.images.all()  # assuming a reverse relation: `related_name='images'` in ProductImage
        return [image.image.url for image in images]


    class Meta:
        model = ProductVariant
        fields = [
            'id', 'color', 'size', 'volume', 'taste',
            'price', 'discount_price', 'discount_percent',
            'stock', 'is_active', 'images', 'product_name'
        ]


class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, required=False)
    variants = ProductVariantSerializer(many=True)

    class Meta:
        model = Product
        fields = [
            'id', 'shop', 'category', 'product_name_uz', 'product_name_ru',
            'description_uz', 'description_ru', 'created_at', 'updated_at',
            'images', 'variants', 'prepayment_amount'
        ]

    def create(self, validated_data):
        images_data = validated_data.pop('images', [])
        variants_data = validated_data.pop('variants', [])
        product = Product.objects.create(**validated_data)

        for image_data in images_data:
            ProductImage.objects.create(product=product, **image_data)
        for variants_data in variants_data:
            ProductVariant.objects.create(product=product, **variants_data)
        return product


class ProductPatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = [
            'shop', 'category', 'product_name_uz', 'product_name_ru',
            'description_uz', 'description_ru', 'prepayment_amount',
        ]


class ProductGetSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True)
    variants = ProductVariantGetSerializer(many=True)
    category = ProductCategorySerializer()
    me_favorite = serializers.SerializerMethodField()

    def get_me_favorite(self, obj):
        user = self.context.get('user')
        if not user:
            return False
        return FavoriteProduct.objects.filter(product=obj, user=user).exists()

    class Meta:
        model = Product
        fields = [
            'id', 'shop', 'category', 'product_name',
            'description', 'created_at', 'updated_at',
            'images', 'variants', 'me_favorite', 'prepayment_amount'
        ]
