from rest_framework import status, permissions, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import BotUser, UserAddress
from .serializers import BotUserSerializer, SetActiveShopSerializer, UserAddressSerializer


class BotUserRegisterView(APIView):
    def post(self, request):
        serializer = BotUserSerializer(data=request.data)

        if not serializer.is_valid():
            return Response({"detail": "Invalid data", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        phone_number = serializer.validated_data['phone_number']
        telegram_id = serializer.validated_data['telegram_id']
        first_name = serializer.validated_data.get('first_name')
        last_name = serializer.validated_data.get('last_name')
        username = serializer.validated_data.get('telegram_username')
        language = serializer.validated_data.get('language', 'uz')

        # Telegram ID bo‘yicha foydalanuvchi borligini tekshirish
        if BotUser.objects.filter(telegram_id=telegram_id).exists():
            return Response({"detail": "User with this telegram_id already exists."}, status=status.HTTP_200_OK)

        # Foydalanuvchi borligini tekshirish yoki yangi foydalanuvchi yaratish
        user, created = BotUser.objects.get_or_create(phone_number=phone_number)
        user.telegram_id = telegram_id
        user.first_name = first_name
        user.last_name = last_name
        user.telegram_username = username
        user.language = language
        user.save()

        return Response({"detail": "User registered successfully. Verification code sent."},
                        status=status.HTTP_201_CREATED)


class BotUserDetailView(APIView):
    def get(self, request, telegram_id):
        try:
            user = BotUser.objects.get(telegram_id=telegram_id)
        except BotUser.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = BotUserSerializer(user)
        return Response(serializer.data)

    def patch(self, request, telegram_id):
        try:
            user = BotUser.objects.get(telegram_id=telegram_id)
        except BotUser.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        data = request.data.copy()
        addresses_data = data.pop("addresses", None)  # alohida ajratib olamiz

        serializer = BotUserSerializer(user, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()

            # ❗Manzillarni faqat YANGILARINI qo‘shamiz (eski manzillar o‘chirilmadi)
            if addresses_data:
                for addr_data in addresses_data:
                    UserAddress.objects.create(user=user, **addr_data)

            return Response(BotUserSerializer(user).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SetActiveShopAPIView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = SetActiveShopSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"detail": "Aktiv do‘kon muvaffaqiyatli yangilandi."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class AddressDetailView(APIView):
    def delete(self, request, *args, **kwargs):
        obj = UserAddress.objects.filter(id=self.kwargs.get('pk')).first()
        if obj:
            obj.delete()
            return Response({"detail": "Address deleted."}, status=status.HTTP_200_OK)
        else:
            return Response({"detail": "Address not found."}, status=status.HTTP_404_NOT_FOUND)

