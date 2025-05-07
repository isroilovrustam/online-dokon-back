from rest_framework import status, permissions, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from .models import BotUser
from .serializers import (
    BotUserSerializer,
    BotUserProfileUpdateSerializer,
    PhoneVerificationSerializer, SetActiveShopSerializer)


class BotUserRegisterView(APIView):
    def post(self, request):
        serializer = BotUserSerializer(data=request.data)

        # Agar serializer xato bo'lsa, xatolikni batafsil ko'rsatish
        if not serializer.is_valid():
            return Response({"detail": "Invalid data", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        phone_number = serializer.validated_data['phone_number']
        telegram_id = serializer.validated_data['telegram_id']

        # Telegram ID bo‘yicha foydalanuvchi borligini tekshirish
        if BotUser.objects.filter(telegram_id=telegram_id).exists():
            return Response({"detail": "User with this telegram_id already exists."}, status=status.HTTP_200_OK)

        # Foydalanuvchi borligini tekshirish yoki yangi foydalanuvchi yaratish
        user, created = BotUser.objects.get_or_create(phone_number=phone_number)
        user.telegram_id = telegram_id
        user.save()

        # Tasdiqlash kodi yaratish
        user.create_verify_code()

        return Response({"detail": "User registered successfully. Verification code sent."},
                        status=status.HTTP_201_CREATED)


class VerifyCode(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        verify_serializer = PhoneVerificationSerializer(data=request.data)
        if not verify_serializer.is_valid():
            return Response(verify_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        phone_number = verify_serializer.validated_data['phone_number']
        code = verify_serializer.validated_data['code']

        try:
            user = BotUser.objects.get(phone_number=phone_number)
        except BotUser.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        confirmation = user.confirmation
        if confirmation.verify_code(code):
            profile_serializer = BotUserProfileUpdateSerializer(user, data=request.data, partial=True)
            if profile_serializer.is_valid():
                profile_serializer.save()
                return Response({"detail": "User profile created successfully."}, status=status.HTTP_200_OK)
            return Response(profile_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        if timezone.now() > confirmation.expiration_time:
            user.create_verify_code()
            return Response({"detail": "Verification code expired. A new code has been sent."},
                            status=status.HTTP_400_BAD_REQUEST)

        return Response({"detail": "Invalid code."}, status=status.HTTP_400_BAD_REQUEST)


class BotUserDetailView(APIView):
    def get(self, request, telegram_id):
        try:
            user = BotUser.objects.get(telegram_id=telegram_id)
        except BotUser.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = BotUserSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class GetUserPhoneView(APIView):
    def get(self, request, telegram_id):
        try:
            user = BotUser.objects.get(telegram_id=telegram_id)
            return Response({"phone_number": user.phone_number}, status=status.HTTP_200_OK)
        except BotUser.DoesNotExist:
            return Response({"detail": "Foydalanuvchi topilmadi"}, status=status.HTTP_404_NOT_FOUND)


class GetVerificationCodeView(APIView):
    def get(self, request, telegram_id):
        try:
            user = BotUser.objects.get(telegram_id=telegram_id)
            confirmation = getattr(user, "confirmation", None)
            if confirmation and not confirmation.is_confirmed:
                return Response({"verification_code": confirmation.code}, status=status.HTTP_200_OK)
            return Response({"detail": "Kod topilmadi yoki allaqachon tasdiqlangan"},
                            status=status.HTTP_400_BAD_REQUEST)
        except BotUser.DoesNotExist:
            return Response({"detail": "Foydalanuvchi topilmadi"}, status=status.HTTP_404_NOT_FOUND)


class SetActiveShopAPIView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = SetActiveShopSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"detail": "Aktiv do‘kon muvaffaqiyatli yangilandi."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




