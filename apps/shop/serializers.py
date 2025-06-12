# serializers.py
from rest_framework import serializers

from botuser.models import BotUser
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
        fields = ['owner', 'shop_name', 'shop_name_uz', 'shop_name_ru', 'phone_number', 'shop_code', 'description',
                  'description_uz',
                  'description_ru', 'shop_logo', 'telegram_group',
                  'telegram_channel', 'instagram_url', 'is_active', 'subscription_start', 'subscription_end',
                  'shop_type', 'addresses']


class ShopGetSerializer(serializers.ModelSerializer):
    addresses = ShopGetAddressSerializer(many=True, required=False)
    shop_logo = serializers.SerializerMethodField()  # Bu qo'shilishi kerak!

    class Meta:
        model = Shop
        fields = ['owner', 'shop_name', 'shop_name_uz', 'shop_name_ru', 'phone_number', 'shop_code', 'description',
                  'description_uz',
                  'description_ru',
                  'shop_logo', 'telegram_group',
                  'telegram_channel', 'instagram_url',
                  'is_active', 'subscription_start', 'subscription_end', 'shop_type', 'addresses']

    def get_shop_logo(self, obj):
        if obj.shop_logo:
            return f"media/{obj.shop_logo.name}"
        return None


class ShopCheckSerializer(serializers.ModelSerializer):
    is_active = serializers.BooleanField()

    class Meta:
        model = Shop
        fields = ['shop_code', 'is_active']


class BasketSerializer(serializers.ModelSerializer):
    telegram_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Basket
        fields = ['telegram_id', 'shop', 'product_variant', 'quantity']

    def create(self, validated_data):
        telegram_id = validated_data.pop('telegram_id')
        try:
            user = BotUser.objects.get(telegram_id=telegram_id)
        except BotUser.DoesNotExist:
            raise serializers.ValidationError("Foydalanuvchi topilmadi.")

        return Basket.objects.create(user=user, **validated_data)


class BasketPathSerializer(serializers.ModelSerializer):
    class Meta:
        model = Basket
        fields = ['quantity', ]


class BasketGetSerializer(serializers.ModelSerializer):
    product_variant = ProductVariantGetSerializer()

    class Meta:
        model = Basket
        fields = ['id', 'product_variant', 'quantity']
