from django.db import models
from product.models import Product, ProductVariant
from shop.models import Shop

ORDINARY_USER, ADMIN = ("ordinary_user", "admin")
UZ, RU = ("uz", "ru")


class BotUser(models.Model):
    USER_ROLES = (
        (ORDINARY_USER, ORDINARY_USER),
        (ADMIN, ADMIN),
    )
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


class UserAddress(models.Model):
    user = models.ForeignKey(BotUser, on_delete=models.CASCADE, related_name='addresses')  # Manzil kimga tegishli
    full_address = models.CharField(max_length=255, null=True, blank=True)  # Manzil (matn shaklida)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.full_name} {self.full_address}"


class ReceptionMethod(models.Model):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='reception_methods')
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name


class Order(models.Model):
    STATUS_CHOICES = [
        ('new', 'Yangi'),
        ('confirmed', 'Tasdiqlandi'),
        ('shipped', 'Jo‘natildi'),
        ('delivered', 'Yetkazildi'),
        ('cancelled', 'Bekor qilindi'),
    ]
    PAYMENT_TYPE = [
        ('Naqd', 'Naqd'),
        ('Karta', 'Karta'),
    ]

    user = models.ForeignKey(BotUser, on_delete=models.CASCADE, related_name='orders')  # Buyurtmachining o‘zi
    longitude = models.FloatField()
    latitude = models.FloatField()
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPE, default='Naqd')
    reception_method = models.ForeignKey(ReceptionMethod, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')  # Buyurtma holati
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # Umumiy narx
    comment = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.id} - {self.user}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')  # Qaysi buyurtmaga tegishli
    product_variant = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL,
                                        null=True)  # Mahsulot o‘chirilganda ham saqlanadi
    quantity = models.PositiveIntegerField(default=1)  # Miqdori (nechta)

    def __str__(self):
        return f"{self.product_variant} x {self.quantity}"


class FavoriteProduct(models.Model):
    user = models.ForeignKey(BotUser, on_delete=models.CASCADE,
                             related_name='favorite_products')  # Qaysi foydalanuvchiga tegishli
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='favorited_by')  # Qaysi mahsulot
    added_at = models.DateTimeField(auto_now_add=True)  # Qachon yoqtirilgani

    # shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='favorited_by')

    class Meta:
        unique_together = ('user', 'product')  # Har bir foydalanuvchi mahsulotni faqat 1 marta yoqtira oladi

    def __str__(self):
        return f"{self.user.phone_number} ❤️ {self.product}"


class ReklamaAdmin(models.Model):
    image = models.FileField(upload_to='reklama_admins/')
    link = models.CharField(max_length=303)

    def __str__(self):
        return f"admin-reklam"


class ReklamaBotUser(models.Model):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='reklama')
    image = models.FileField(upload_to='reklama_admins/')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reklama')

    def __str__(self):
        return f"{self.shop}-{self.product}-reklama"
