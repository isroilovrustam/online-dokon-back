# serializers.py
from rest_framework import serializers
from shop.models import Shop, ShopAddress


class ShopAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShopAddress
        fields = ['id', 'full_address', 'label']


class ShopSerializer(serializers.ModelSerializer):
    addresses = ShopAddressSerializer(many=True, read_only=True)  # Shop.related_name = 'addresses' ishlatilgan

    class Meta:
        model = Shop
        fields = ['shop_name', 'phone_number', 'description', 'shop_logo', 'telegram_channel', 'instagram_url',
                  'shop_type', 'addresses']


class ShopCheckSerializer(serializers.ModelSerializer):
    is_active = serializers.BooleanField()

    class Meta:
        model = Shop
        fields = ['shop_code', 'is_active']

