# serializers.py
from rest_framework import serializers
from shop.models import Shop, ShopAddress, Basket
from product.serializers import ProductVariantGetSerializer


class ShopAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShopAddress
        fields = ['id', 'full_address_uz', 'full_address_ru']


class ShopGetAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShopAddress
        fields = ['id', 'full_address']


class ShopSerializer(serializers.ModelSerializer):
    addresses = ShopAddressSerializer(many=True, required=False)  # Shop.related_name = 'addresses' ishlatilgan

    class Meta:
        model = Shop
        fields = ['owner', 'shop_name', 'shop_name_uz', 'shop_name_ru', 'phone_number', 'shop_code', 'description_uz',
                  'description_ru', 'description', 'shop_logo', 'telegram_group',
                  'telegram_channel', 'instagram_url', 'is_active', 'subscription_start', 'subscription_end',
                  'shop_type', 'addresses']


class ShopGetSerializer(serializers.ModelSerializer):
    addresses = ShopGetAddressSerializer(many=True, required=False)

    class Meta:
        model = Shop
        fields = ['owner', 'shop_name', 'shop_name_uz', 'shop_name_ru', 'phone_number', 'shop_code', 'description_uz',
                  'description_ru', 'description',
                  'shop_logo', 'telegram_group',
                  'telegram_channel', 'instagram_url',
                  'is_active', 'subscription_start', 'subscription_end', 'shop_type', 'addresses']


class ShopCheckSerializer(serializers.ModelSerializer):
    is_active = serializers.BooleanField()

    class Meta:
        model = Shop
        fields = ['shop_code', 'is_active']


class BasketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Basket
        fields = ['user', 'shop', 'product_variant', 'quantity']
class BasketPathSerializer(serializers.ModelSerializer):
    class Meta:
        model = Basket
        fields = ['quantity']


class BasketGetSerializer(serializers.ModelSerializer):
    product_variant = ProductVariantGetSerializer()

    class Meta:
        model = Basket
        fields = ['product_variant', 'quantity']
