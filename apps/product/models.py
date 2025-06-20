from django.db import models

from shop.models import Shop


class ProductCategory(models.Model):
    name = models.CharField(max_length=100)
    image = models.FileField(upload_to='product_category_image/', null=True, blank=True)
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='categories')

    def __str__(self):
        return self.name

    class Meta:
        unique_together = ('name', 'shop')


class ProductColor(models.Model):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='colors')
    color = models.CharField(max_length=100)

    def __str__(self):
        return self.color


class ProductSize(models.Model):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='sizes')
    size = models.CharField(max_length=100)

    def __str__(self):
        return self.size


class ProductTaste(models.Model):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='tastes')
    taste = models.CharField(max_length=100)

    def __str__(self):
        return self.taste


class ProductVolume(models.Model):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='volumes')
    volume = models.CharField(max_length=100)

    def __str__(self):
        return self.volume


class Product(models.Model):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='products', verbose_name="Do‘kon")
    category = models.ForeignKey(ProductCategory, on_delete=models.SET_NULL, null=True, related_name='products')
    product_name = models.CharField(max_length=255, verbose_name="Mahsulot nomi")
    description = models.TextField(blank=True, null=True, verbose_name="Qisqacha tavsif")

    prepayment_amount = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="Agar oldindan to‘lov talab qilinsa, shu yerga summani kiriting"
    )
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
    color = models.ForeignKey(ProductColor, on_delete=models.SET_NULL, null=True, blank=True)
    size = models.ForeignKey(ProductSize, on_delete=models.SET_NULL, null=True, blank=True)
    volume = models.ForeignKey(ProductVolume, on_delete=models.SET_NULL, null=True, blank=True)
    taste = models.ForeignKey(ProductTaste, on_delete=models.SET_NULL, null=True, blank=True)

    price = models.CharField(max_length=30, verbose_name="Asl narx (so'm)", null=True, blank=True)
    discount_price = models.CharField(max_length=30, blank=True, null=True,
                                      verbose_name="Chegirma narxi (so'm)")
    discount_percent = models.PositiveIntegerField(blank=True, null=True, verbose_name="Chegirma foizi (%)")

    stock = models.PositiveIntegerField(default=0, verbose_name="Ombordagi soni")
    is_active = models.BooleanField(default=True, verbose_name="Faol holatda")

    class Meta:
        unique_together = ('product', 'color', 'size', 'volume', 'taste')

    def __str__(self):
        return f"{self.product.product_name} | Rang: {self.color} | Razmer: {self.size or '-'} | Hajm: {self.volume or '-'} | Ta’m: {self.taste or '-'}"
