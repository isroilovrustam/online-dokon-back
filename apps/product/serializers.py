from django.contrib.sites import requests
from django.db.models import Sum
from rest_framework import serializers
from botuser.models import FavoriteProduct, Order, OrderItem
from botuser.serializers import BotUserSerializer
from config.settings import BOT_B_TOKEN
from shop.models import Basket, Shop
from .models import ProductImage, ProductVariant, Product, ProductVolume, ProductSize, ProductTaste, ProductColor, \
    ProductCategory


class ProductCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductCategory
        fields = ["id", "name_uz", "name_ru", "image", "shop"]


class ProductGetCategorySerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = ProductCategory
        fields = ["id", "name", "name_uz", "name_ru", "image", "shop"]

    def get_image(self, obj):
        if obj.image:
            return f"media/{obj.image.name}"
        return None


class ProductColorSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductColor
        fields = ["id", 'shop', "color", "color_uz", "color_ru"]


class ProductSizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductSize
        fields = ["id", 'shop', "size"]


class ProductTasteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductTaste
        fields = ["id", 'shop', "taste", "taste_uz", "taste_uz"]


class ProductVolumeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVolume
        fields = ["id", 'shop', "volume"]


class ProductCreateImageSerializer(serializers.ModelSerializer):
    # image = serializers.SerializerMethodField()

    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'product']


class ProductImageSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'product']

    def get_image(self, obj):
        # `media/` dan boshlab to‘liq nisbiy pathni olish
        if obj.image:
            return f"media/{obj.image.name}"
        return None


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
            'id', 'color', 'size', 'volume', 'taste',
            'product', 'price', 'discount_price', 'discount_percent',
            'stock', 'is_active'
        ]


class ProductVariantGetSerializer(serializers.ModelSerializer):
    color = ProductColorSerializer()
    size = ProductSizeSerializer()
    volume = ProductVolumeSerializer()
    taste = ProductTasteSerializer()
    images = serializers.SerializerMethodField()
    product_name = serializers.SerializerMethodField()
    quantity = serializers.SerializerMethodField()

    def get_product_name(self, obj):
        return obj.product.product_name if obj.product else None

    def get_images(self, obj):
        images = obj.product.images.all()  # assuming a reverse relation: `related_name='images'` in ProductImage
        return [image.image.url if image.image else None for image in images]

    def get_quantity(self, obj):
        user = self.context.get('user')
        if not user:
            return 0
        return Basket.objects.filter(user=user, product_variant=obj).aggregate(total=Sum('quantity'))['total'] or 0

    class Meta:
        model = ProductVariant
        fields = [
            'id', 'color', 'size', 'volume', 'taste',
            'price', 'discount_price', 'discount_percent',
            'stock', 'is_active', 'images', 'product_name', 'quantity'
        ]


class ProductSerializer(serializers.ModelSerializer):
    # variants = ProductVariantSerializer(many=True, required=False)
    shop = serializers.SlugRelatedField(
        queryset=Shop.objects.all(),
        slug_field='shop_code'
    )

    class Meta:
        model = Product
        fields = [
            'id', 'shop', 'category', 'product_name_uz', 'product_name_ru',
            'description_uz', 'description_ru', 'created_at', 'updated_at',
            'prepayment_amount'
        ]


class ProductPatchSerializer(serializers.ModelSerializer):
    quantity = serializers.IntegerField(write_only=True, required=False, min_value=0)
    variant_id = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = Product
        fields = [
            'shop', 'category', 'product_name_uz', 'product_name_ru',
            'description_uz', 'description_ru', 'prepayment_amount', 'quantity',
            'variant_id'
        ]

    def update(self, instance, validated_data):
        quantity = validated_data.pop('quantity', None)
        variant_id = validated_data.pop('variant_id', None)
        user = self.context.get('user')

        if quantity is not None and variant_id and user:
            variant = ProductVariant.objects.filter(id=variant_id, product=instance).first()
            if variant:
                if quantity == 0:
                    # 🔴 Miqdor 0 bo‘lsa – savatdan o‘chirish
                    Basket.objects.filter(user=user, product_variant=variant).delete()
                else:
                    # ✅ Aks holda yangilash yoki yaratish
                    basket, _ = Basket.objects.get_or_create(user=user, product_variant=variant)
                    basket.quantity = quantity
                    basket.save()

        # Boshqa maydonlar ham yangilanadi (agar mavjud bo‘lsa)
        return super().update(instance, validated_data)


class ProductGetSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True)
    variants = ProductVariantGetSerializer(many=True)
    category = ProductCategorySerializer()
    me_favorite = serializers.SerializerMethodField()
    quantity = serializers.SerializerMethodField()

    def get_me_favorite(self, obj):
        user = self.context.get('user')
        if not user:
            return False
        return FavoriteProduct.objects.filter(product=obj, user=user).exists()

    def get_quantity(self, obj):
        user = self.context.get('user')
        if not user:
            return 0

        # Shu productga tegishli barcha variantlar uchun foydalanuvchining savatdagi quantity summasi
        return Basket.objects.filter(
            user=user,
            product_variant__product=obj
        ).aggregate(total=Sum('quantity'))['total'] or 0

    class Meta:
        model = Product
        fields = [
            'id', 'shop', 'category', 'product_name', "product_name_uz", "product_name_ru",
            'description', "description_uz", "description_ru", 'created_at', 'updated_at',
            'images', 'variants', 'me_favorite', 'quantity', 'prepayment_amount'
        ]


class OrderItemSerializer(serializers.ModelSerializer):
    product_variant = ProductVariantGetSerializer()

    class Meta:
        model = OrderItem
        fields = ['id', 'product_variant', 'quantity', 'product_variant']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    user = BotUserSerializer(read_only=True)

    status_display = serializers.SerializerMethodField()
    payment_display = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'id', 'longitude', 'latitude', 'address',
            'payment_type', "payment_display", "status_display", 'reception_method', 'created_at',
            'status', 'total_price', 'comment', 'user', 'items'
        ]

    def get_status_display(self, obj):
        translations = {
            'new': {'uz': 'Yangi', 'ru': 'Новый'},
            'confirmed': {'uz': 'Tasdiqlandi', 'ru': 'Подтвержден'},
            'shipped': {'uz': 'Jo‘natildi', 'ru': 'Отправлен'},
            'delivered': {'uz': 'Yetkazildi', 'ru': 'Доставлен'},
            'cancelled': {'uz': 'Bekor qilindi', 'ru': 'Отменен'},
        }
        return translations.get(obj.status, {
            'uz': obj.status,
            'ru': obj.status
        })

    def get_payment_display(self, obj):
        translations = {
            'Naqd': {'uz': 'Naqd', 'ru': 'Наличные'},
            'Karta': {'uz': 'Karta', 'ru': 'Карта'},
        }
        return translations.get(obj.payment_type, {
            'uz': obj.payment_type,
            'ru': obj.payment_type
        })

class OrderStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['status']

    def validate_status(self, value):
        valid_statuses = [choice[0] for choice in Order.STATUS_CHOICES]
        if value not in valid_statuses:
            raise serializers.ValidationError("Noto‘g‘ri status qiymati.")
        return value
