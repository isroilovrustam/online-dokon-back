from rest_framework import serializers
from shop.models import Shop
from .models import BotUser, UserAddress, ReceptionMethod


class ReceptionMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReceptionMethod
        fields = '__all__'


class UserAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAddress
        fields = ["id", "full_address", "created_at"]
        read_only_fields = ["id", "created_at"]


class BotUserSerializer(serializers.ModelSerializer):
    addresses = UserAddressSerializer(many=True, required=False)
    active_shop = serializers.SerializerMethodField()

    def get_active_shop(self, obj):
        if obj.active_shop is not None:
            return {
                "shop_code": obj.active_shop.shop_code,
                "shop_name": obj.active_shop.shop_name,
                "is_active": obj.active_shop.is_active,
                "group_id": obj.active_shop.telegram_group,
                "phone_number": obj.active_shop.phone_number,
            }
        return None

    class Meta:
        model = BotUser
        fields = ["user_roles", "active_shop", "phone_number", "telegram_id", "first_name",
                  "last_name", "telegram_username", "language", 'addresses']


class SetActiveShopSerializer(serializers.Serializer):
    telegram_id = serializers.CharField(max_length=32)
    shop_code = serializers.CharField(max_length=32)

    def validate(self, attrs):
        telegram_id = attrs.get("telegram_id")
        shop_code = attrs.get("shop_code")

        try:
            user = BotUser.objects.get(telegram_id=telegram_id)
        except BotUser.DoesNotExist:
            raise serializers.ValidationError({"telegram_id": "Foydalanuvchi topilmadi."})

        try:
            shop = Shop.objects.get(shop_code=shop_code)
        except Shop.DoesNotExist:
            raise serializers.ValidationError({"shop_code": "Do‘kon topilmadi."})

        attrs["user"] = user
        attrs["shop"] = shop
        return attrs

    def save(self, **kwargs):
        user = self.validated_data["user"]
        shop = self.validated_data["shop"]
        user.active_shop = shop
        user.save(update_fields=["active_shop"])
        return user


class ReklamaSerializer(serializers.Serializer):
    image = serializers.ImageField()
    link = serializers.CharField(allow_null=True, required=False)
    product_id = serializers.IntegerField(allow_null=True, required=False)
