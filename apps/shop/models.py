from django.db import models
from django.utils import timezone


ONLINE, OFFLINE, BOTH = ('online', 'offline', 'both')


class Shop(models.Model):
    SHOP_TYPES = (
        (ONLINE, 'Faqar online'),
        (OFFLINE, 'Faqat offline'),
        (BOTH, 'Online va offline'),
    )

    owner = models.ForeignKey('botuser.BotUser', on_delete=models.CASCADE, related_name='shops')
    shop_name = models.CharField(max_length=150)  # Do'kon nomi
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    shop_code = models.CharField(max_length=100,
                                 unique=True)  # Do'kon koddi yani shu do'kon uchun alohida link beriladi shu link orqali botga start bosganda faqat shu do'kon mahsulotlari ko'rinishi uchun
    description = models.TextField(blank=True, null=True)  # Do'kon haqida qisqacha
    shop_logo = models.ImageField(upload_to='shop_logos/', null=True, blank=True)  # Do'kon logotipi
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
    label = models.CharField(max_length=100, blank=True, null=True)  # Masalan: Asosiy filial, Yunusobod filial

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.shop.shop_name} - {self.label or 'Filial'} - {self.full_address}"


class Cart(models.Model):
    user = models.ForeignKey('botuser.BotUser', on_delete=models.CASCADE)
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'shop')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def update_total_price(self):
        total = sum(item.quantity * item.price for item in self.items.all())
        self.total_price = total
        self.save()

    def add_product(self, product, quantity=1):
        item, created = CartItem.objects.get_or_create(
            cart=self, product=product,
            defaults={'quantity': quantity, 'price': product.price}
        )
        if not created:
            item.quantity += quantity
            item.save()
        self.update_total_price()

    def remove_product(self, product):
        try:
            item = CartItem.objects.get(cart=self, product=product)
            item.delete()
        except CartItem.DoesNotExist:
            pass
        self.update_total_price()

    def clear_cart(self):
        self.items.all().delete()
        self.update_total_price()

    def __str__(self):
        return f"{self.user} - {self.shop.shop_name}"

    product_volume = models.CharField(max_length=50, null=True, blank=True)


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('product.Product', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.product.product_name} ({self.quantity})"
