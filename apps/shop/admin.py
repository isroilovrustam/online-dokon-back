from django.contrib import admin
from .models import Shop, ShopAddress, Basket
from .translations import CustomAdmin


class ShopAddressInline(admin.TabularInline):
    model = ShopAddress
    extra = 1  # Yangi address qo‘shish uchun 1 ta bo‘sh form
    fields = ('full_address',)
    show_change_link = True


@admin.register(Shop)
class ShopAdmin(CustomAdmin):
    list_display = ('shop_name', 'owner', 'shop_code', 'is_active', 'is_subscription_active', 'shop_type', 'created_at')
    list_filter = ('is_active', 'shop_type', 'created_at')
    search_fields = ('shop_name', 'shop_code', 'owner__first_name', 'owner__last_name', 'phone_number')
    readonly_fields = ('created_at', 'updated_at', 'is_subscription_active')
    inlines = [ShopAddressInline]
    fieldsets = (
        ('Do‘kon ma’lumotlari', {
            'fields': ('shop_name', 'owner', 'phone_number', 'shop_code', 'description', 'shop_logo', 'shop_type')
        }),
        ('Telegram / Instagram', {
            'fields': ('telegram_group', 'telegram_channel', 'instagram_url')
        }),
        ('Holat va abonement', {
            'fields': ('is_active', 'subscription_start', 'subscription_end', 'is_subscription_active')
        }),
        ('Tizim maydonlari', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(Basket)
class BasketAdmin(admin.ModelAdmin):
    list_display = ('user', 'shop', 'product', 'quantity', 'created_at')
    list_filter = ('shop', 'created_at')
    search_fields = ('user__id', 'shop__shop_name', 'product__product_name')
    autocomplete_fields = ('user', 'shop', 'product')  # Katta ma'lumot bo‘lsa qulay bo‘ladi
    readonly_fields = ('created_at', 'updated_at')


@admin.register(ShopAddress)
class ShopAddressAdmin(CustomAdmin):
    list_display = ('shop', 'full_address', 'created_at')
    search_fields = ('shop__shop_name', 'full_address')
    list_filter = ('created_at',)
