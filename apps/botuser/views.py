from rest_framework import status, permissions, generics, viewsets
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework.generics import CreateAPIView, DestroyAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from shop.models import Shop
from .models import BotUser, UserAddress, ReklamaBotUser, ReklamaAdmin, ReceptionMethod
from .serializers import BotUserSerializer, SetActiveShopSerializer, ReklamaSerializer, UserAddressSerializer, \
    ReceptionMethodSerializer, ReklamaCreateSerializer


class ReceptionMethodListCreateAPIView(generics.ListCreateAPIView):
    queryset = ReceptionMethod.objects.all()
    serializer_class = ReceptionMethodSerializer


class ReceptionMethodDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = ReceptionMethod.objects.all()
    serializer_class = ReceptionMethodSerializer


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
        active_shop = serializer.validated_data.get('active_shop')

        # Telegram ID bo‘yicha foydalanuvchi borligini tekshirish
        if BotUser.objects.filter(telegram_id=telegram_id).exists():
            return Response({"detail": "User with this telegram_id already exists."}, status=status.HTTP_200_OK)

        # Foydalanuvchi borligini tekshirish yoki yangi foydalanuvchi yaratish
        user, created = BotUser.objects.get_or_create(phone_number=phone_number, defaults={"telegram_id": telegram_id})
        user.telegram_id = telegram_id
        user.first_name = first_name
        user.last_name = last_name
        user.telegram_username = username
        user.language = language
        user.active_shop = active_shop
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


class AddressCreateByTelegramView(APIView):
    def post(self, request, *args, **kwargs):
        telegram_id = kwargs.get("telegram_id")
        user = BotUser.objects.filter(telegram_id=telegram_id).first()
        if not user:
            return Response({"detail": "User with this Telegram ID not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = UserAddressSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=user)  # Aynan shu userga bog‘laymiz
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ReklamaListView(generics.ListAPIView):
    serializer_class = ReklamaSerializer

    def get(self, request, *args, **kwargs):
        qs = ReklamaBotUser.objects.filter(shop__shop_code=self.kwargs.get('shop_code'))
        ls = list()
        for i in qs:
            ls.append(ReklamaSerializer(i).data)
        qs = ReklamaAdmin.objects.all()
        for i in qs:
            ls.append(ReklamaSerializer(i).data)
        return Response(ls)

    lookup_url_kwarg = "shop_code"


class ReklamaCreateView(CreateAPIView):
    queryset = ReklamaBotUser.objects.all()
    serializer_class = ReklamaCreateSerializer

    def perform_create(self, serializer):
        telegram_id = self.request.data.get('telegram_id')
        if not telegram_id:
            raise ValidationError({'telegram_id': 'required'})

        try:
            user = BotUser.objects.get(telegram_id=telegram_id)
        except BotUser.DoesNotExist:
            raise ValidationError({'telegram_id': 'User not found'})

        try:
            shop = Shop.objects.get(owner=user)
        except Shop.DoesNotExist:
            raise ValidationError({'shop': 'No shop found for this user.'})

        serializer.save(shop=shop)


class ReklamaDeleteView(DestroyAPIView):
    queryset = ReklamaBotUser.objects.all()

    def delete(self, request, *args, **kwargs):
        telegram_id = request.data.get("telegram_id")
        if not telegram_id:
            raise ValidationError({'telegram_id': 'required'})

        try:
            user = BotUser.objects.get(telegram_id=telegram_id)
        except BotUser.DoesNotExist:
            raise ValidationError({'telegram_id': 'User not found'})

        try:
            shop = Shop.objects.get(owner=user)
        except Shop.DoesNotExist:
            raise ValidationError({'shop': 'No shop found for this user.'})

        instance = self.get_object()
        if instance.shop != shop:
            raise PermissionDenied("Siz faqat o'zingizga tegishli reklamalarni o'chira olasiz.")

        return self.destroy(request, *args, **kwargs)