from django.db import models

from shop.models import Shop


class ProductCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    image = models.FileField(upload_to='product_category_image/', null=True, blank=True)

    def __str__(self):
        return self.name


class ProductColor(models.Model):
    color = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.color


class ProductSize(models.Model):
    size = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.size


class ProductTaste(models.Model):
    taste = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.taste


class ProductVolume(models.Model):
    volume = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.volume


class Product(models.Model):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='products', verbose_name="Do‘kon")
    category = models.ForeignKey(ProductCategory, on_delete=models.SET_NULL, null=True, related_name='products')
    product_name = models.CharField(max_length=255, verbose_name="Mahsulot nomi")
    description = models.TextField(blank=True, null=True, verbose_name="Qisqacha tavsif")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.product_name


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.FileField(upload_to='product_images')

    def __str__(self):
        return f"Rasm: {self.product.product_name}"


class ProductVariant(models.Model):
    product = models.ForeignKey(Product, related_name='variants', on_delete=models.CASCADE)
    color = models.ForeignKey(ProductColor, on_delete=models.CASCADE)
    size = models.ForeignKey(ProductSize, on_delete=models.CASCADE, null=True, blank=True)
    volume = models.ForeignKey(ProductVolume, on_delete=models.CASCADE, null=True, blank=True)
    taste = models.ForeignKey(ProductTaste, on_delete=models.CASCADE, null=True, blank=True)

    price = models.DecimalField(max_digits=30, decimal_places=2, verbose_name="Asl narx (so'm)")
    discount_price = models.DecimalField(max_digits=30, decimal_places=2, blank=True, null=True,
                                         verbose_name="Chegirma narxi (so'm)")
    discount_percent = models.PositiveIntegerField(blank=True, null=True, verbose_name="Chegirma foizi (%)")
    prepayment_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Agar oldindan to‘lov talab qilinsa, shu yerga summani kiriting"
    )
    stock = models.PositiveIntegerField(default=0, verbose_name="Ombordagi soni")
    is_active = models.BooleanField(default=True, verbose_name="Faol holatda")

    class Meta:
        unique_together = ('product', 'color', 'size', 'volume', 'taste')

    def __str__(self):
        return f"{self.product.product_name} | Rang: {self.color} | Razmer: {self.size or '-'} | Hajm: {self.volume or '-'} | Ta’m: {self.taste or '-'}"

    def has_discount(self):
        return self.discount_price and self.discount_price < self.price

    def get_discount_percent(self):
        if self.has_discount():
            return round(100 - (self.discount_price / self.price) * 100)
        return 0

    def save(self, *args, **kwargs):
        if self.discount_percent and not self.discount_price:
            self.discount_price = self.price * (1 - self.discount_percent / 100)
        elif self.discount_price and not self.discount_percent:
            self.discount_percent = round(100 - (self.discount_price / self.price) * 100)
        super().save(*args, **kwargs)
