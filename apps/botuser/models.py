from django.utils import timezone
from datetime import timedelta
from django.db import models
import random

from rest_framework.exceptions import ValidationError

from product.models import Product
# SMS yoki boshqa bot orqali yuborish (Bot B)
from .utils import send_telegram_message
from django.conf import settings

# Foydalanuvchi rollari va tillari uchun doimiy qiymatlar
ORDINARY_USER, MANAGER, ADMIN = ("ordinary_user", "manager", "admin")
UZ, RU = ("uz", "ru")


class BotUser(models.Model):
    # Foydalanuvchi rollari (oddiy, menejer, admin)
    USER_ROLES = (
        (ORDINARY_USER, ORDINARY_USER),
        (MANAGER, MANAGER),
        (ADMIN, ADMIN),
    )
    # Til tanlovi (o'zbek yoki rus)
    USER_LANGUAGES = (
        (UZ, UZ),
        (RU, RU),
    )

    user_roles = models.CharField(max_length=31, choices=USER_ROLES, default=ORDINARY_USER)
    language = models.CharField(max_length=20, choices=USER_LANGUAGES, default=UZ)

    phone_number = models.CharField(max_length=20, unique=True)  # Telefon raqami (har doim unique)
    telegram_id = models.CharField(max_length=20, unique=True)  # Telegram ID (foydalanuvchini aniqlash uchun)
    telegram_username = models.CharField(max_length=32, null=True, blank=True)  # Telegram username (unique emas)
    first_name = models.CharField(max_length=50, null=True, blank=True)  # Ismi
    last_name = models.CharField(max_length=50, null=True, blank=True)  # Familiyasi

    location = models.CharField(max_length=100, null=True, blank=True)  # Matn ko'rinishida manzil (optional)

    # Foydalanuvchining faol do‘koni (tanlangan)
    active_shop = models.ForeignKey('shop.Shop', on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='active_users')

    created_at = models.DateTimeField(auto_now_add=True)  # Yaratilgan sana
    updated_at = models.DateTimeField(auto_now=True)  # Oxirgi yangilangan vaqti

    def __str__(self):
        return self.phone_number  # Admin panelda ko‘rinadigan matn

    @property
    def full_name(self):
        # To‘liq ism (bo‘sh joy bilan birlashtiriladi)
        return f"{self.first_name or ''} {self.last_name or ''}".strip()

    def create_verify_code(self):
        # Tasdiqlash kodi yaratish (4 xonali)
        code = "".join([str(random.randint(0, 9)) for _ in range(4)])

        # Yangi yoki mavjud kodni yangilash
        confirmation, created = UserConfirmation.objects.update_or_create(
            user=self,
            defaults={
                "code": code,
                "expiration_time": timezone.now() + timedelta(minutes=2),  # 2 daqiqalik amal qilish muddati
                "is_confirmed": False
            }
        )

        # Foydalanuvchiga Telegram orqali xabar yuborish
        message = f"🔒 Kodingiz / Ваш код:  {code}"
        send_telegram_message(self.telegram_id, message, settings.BOT_B_TOKEN)
        return code


class UserConfirmation(models.Model):
    user = models.OneToOneField(BotUser, on_delete=models.CASCADE,
                                related_name="confirmation")  # Har bir user uchun 1 ta tasdiqlash kodi
    code = models.CharField(max_length=4)  # 4 xonali tasdiqlash kodi
    expiration_time = models.DateTimeField()  # Amal qilish muddati
    is_confirmed = models.BooleanField(default=False)  # Tasdiqlangan yoki yo‘qligi

    def __str__(self):
        return f"Confirmation for {self.user.phone_number}"

    def verify_code(self, entered_code):
        # Kod to‘g‘ri va hali muddati tugamaganligini tekshirish
        if self.is_confirmed:
            return True

        if timezone.now() > self.expiration_time:
            return False

        if self.code == entered_code:
            self.is_confirmed = True
            self.save()
            return True

        return False


class UserAddress(models.Model):
    user = models.ForeignKey(BotUser, on_delete=models.CASCADE, related_name='addresses')  # Manzil kimga tegishli

    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)  # GPS bo‘yicha latitude
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)  # GPS bo‘yicha longitude

    full_address = models.CharField(max_length=255, null=True, blank=True)  # Manzil (matn shaklida)

    label = models.CharField(max_length=100, blank=True, null=True)  # Masalan: Uy, Ish

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.label or f"Address {self.id}"


class Order(models.Model):
    STATUS_CHOICES = [
        ('new', 'Yangi'),
        ('confirmed', 'Tasdiqlandi'),
        ('shipped', 'Jo‘natildi'),
        ('delivered', 'Yetkazildi'),
        ('cancelled', 'Bekor qilindi'),
    ]

    user = models.ForeignKey(BotUser, on_delete=models.CASCADE, related_name='orders')  # Buyurtmachining o‘zi
    address = models.ForeignKey(UserAddress, on_delete=models.SET_NULL, null=True,
                                blank=True)  # Yetkazib berish manzili
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')  # Buyurtma holati
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # Umumiy narx
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.id} - {self.user}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')  # Qaysi buyurtmaga tegishli
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)  # Mahsulot o‘chirilganda ham saqlanadi
    quantity = models.PositiveIntegerField(default=1)  # Miqdori (nechta)
    price = models.DecimalField(max_digits=10, decimal_places=2)  # O‘sha vaqtdagi mahsulot narxi

    def __str__(self):
        return f"{self.product} x {self.quantity}"



class FavoriteProduct(models.Model):
    user = models.ForeignKey(BotUser, on_delete=models.CASCADE,
                             related_name='favorite_products')  # Qaysi foydalanuvchiga tegishli
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='favorited_by')  # Qaysi mahsulot
    added_at = models.DateTimeField(auto_now_add=True)  # Qachon yoqtirilgani

    class Meta:
        unique_together = ('user', 'product')  # Har bir foydalanuvchi mahsulotni faqat 1 marta yoqtira oladi

    def __str__(self):
        return f"{self.user.phone_number} ❤️ {self.product}"
