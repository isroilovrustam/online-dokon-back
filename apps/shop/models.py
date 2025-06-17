from django.db import models
from django.utils import timezone

ONLINE, OFFLINE, BOTH = ('online', 'offline', 'both')


class Shop(models.Model):
    SHOP_TYPES = (
        (ONLINE, 'Faqat online'),
        (OFFLINE, 'Faqat offline'),
        (BOTH, 'Online va offline'),
    )

    owner = models.ForeignKey('botuser.BotUser', on_delete=models.CASCADE, related_name='shops')
    shop_name = models.CharField(max_length=150)  # Do'kon nomi
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    shop_code = models.CharField(max_length=100, primary_key=True,
                                 unique=True)  # Do'kon koddi yani shu do'kon uchun alohida link beriladi shu link orqali botga start bosganda faqat shu do'kon mahsulotlari ko'rinishi uchun
    description = models.TextField(blank=True, null=True)  # Do'kon haqida qisqacha
    shop_logo = models.ImageField(upload_to='shop_logos/', null=True, blank=True)  # Do'kon logotipi
    uz_card = models.CharField(max_length=100, blank=True, null=True)
    uz_card_holder = models.CharField(max_length=100, blank=True, null=True)
    humo_card = models.CharField(max_length=100, blank=True, null=True)
    humo_card_holder = models.CharField(max_length=100, blank=True, null=True)
    visa_card = models.CharField(max_length=100, blank=True, null=True)
    visa_card_holder = models.CharField(max_length=100, blank=True, null=True)
    telegram_group = models.CharField(max_length=255, blank=True,
                                      null=True)  # Do'konga tushadigon zakazlar telegram guruxiga yuboriladi
    telegram_channel = models.URLField(max_length=255, blank=True, null=True)  # Do'koning telegram kanal linki
    instagram_url = models.URLField(max_length=255, blank=True, null=True)  # Do'koning instagram linki
    is_active = models.BooleanField(
        default=False)  # Do'kon activmi yoki activ emasmi ko'rastib turishi uchun yani bizdan abaniment sotib oladi agar abaniment vaqti o'tib ketgan bo'lsa biz uni activmas qilib qo'yamiz va do'konidan foydalan olmaydi

    # Abonement muddati
    subscription_start = models.DateTimeField(null=True, blank=True)
    subscription_end = models.DateTimeField(null=True, blank=True)

    shop_type = models.CharField(max_length=10, choices=SHOP_TYPES, default=ONLINE)  # Online / Offline / Har ikkisi

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def is_subscription_active(self):
        if self.subscription_end:
            return self.subscription_end > timezone.now()
        return False

    def __str__(self):
        return self.shop_name


# Agar do'kon turi offline yoki both bo'lsa — manzillarni ko‘rsatish uchun
class ShopAddress(models.Model):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='addresses')  # Qaysi do'konga tegishli
    full_address = models.CharField(max_length=255)  # Manzil matn ko'rinishida

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.shop.shop_name} - {self.full_address}"


class Basket(models.Model):
    user = models.ForeignKey('botuser.BotUser', on_delete=models.CASCADE)
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE)
    product_variant = models.ForeignKey('product.ProductVariant', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user_id} - {self.shop.shop_name} - {self.product_variant.product.product_name} ({self.quantity})"
