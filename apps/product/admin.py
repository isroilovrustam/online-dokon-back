from django.contrib import admin
from .translations import CustomAdmin
from .models import (
    ProductCategory, ProductColor, ProductSize, ProductTaste, ProductVolume,
    Product, ProductImage, ProductVariant
)


@admin.register(ProductCategory)
class ProductCategoryAdmin(CustomAdmin):
    list_display = ('id','name',)
    search_fields = ('name',)


@admin.register(ProductColor)
class ProductColorAdmin(CustomAdmin):
    list_display = ('color',)
    search_fields = ('color',)


@admin.register(ProductSize)
class ProductSizeAdmin(admin.ModelAdmin):
    list_display = ('size',)
    search_fields = ('size',)


@admin.register(ProductTaste)
class ProductTasteAdmin(CustomAdmin):
    list_display = ('taste',)
    search_fields = ('taste',)


@admin.register(ProductVolume)
class ProductVolumeAdmin(admin.ModelAdmin):
    list_display = ('volume',)
    search_fields = ('volume',)


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    # readonly_fields = ['image']


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1
    show_change_link = True
    fields = (
        'color', 'size', 'volume', 'taste',
        'price', 'discount_price', 'discount_percent', 'stock', 'is_active'
    )


@admin.register(Product)
class ProductAdmin(CustomAdmin):
    list_display = ('product_name', 'shop', 'category', 'created_at')
    search_fields = ('product_name', 'description')
    list_filter = ('shop', 'category')
    inlines = [ProductImageInline, ProductVariantInline]
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ("Asosiy ma'lumotlar", {
            'fields': ('shop', 'category', 'product_name', 'description')
        }),
        ("Yaratilgan va yangilangan vaqtlar", {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = (
        'product', 'color', 'size', 'volume', 'taste',
        'price', 'discount_price', 'stock', 'is_active'
    )
    list_filter = ('product', 'color', 'size', 'volume', 'taste', 'is_active')
    search_fields = ('product__product_name',)
    readonly_fields = ('get_discount_percent',)
    fieldsets = (
        (None, {
            'fields': ('product', 'color', 'size', 'volume', 'taste')
        }),
        ('Narx va chegirmalar', {
            'fields': ('price', 'discount_price', 'discount_percent', 'get_discount_percent')
        }),
        ('Qo‘shimcha ma’lumotlar', {
            'fields': ('prepayment_amount', 'stock', 'is_active')
        }),
    )

    def get_discount_percent(self, obj):
        return f"{obj.get_discount_percent()}%"

    get_discount_percent.short_description = "Hisoblangan chegirma (%)"


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('product', 'image')
    # readonly_fields = ('image',)
