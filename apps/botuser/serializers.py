from rest_framework import serializers

from product.serializers import ProductSerializer
from shop.models import Shop
from .models import BotUser, FavoriteProduct, UserConfirmation

class UserConfirmationSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserConfirmation
        fields = '__all__'

class BotUserSerializer(serializers.ModelSerializer):
    confirmation = UserConfirmationSerializer(read_only=True)
    class Meta:
        model = BotUser
        fields = ["phone_number", "telegram_id", "first_name",
            "last_name", "telegram_username", "location", "language", "confirmation"]


class BotUserProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = BotUser
        fields = [
            "first_name", "last_name", "telegram_username",
            "location", "language"
        ]


class PhoneVerificationSerializer(serializers.Serializer):
    phone_number = serializers.CharField()
    code = serializers.CharField()



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



