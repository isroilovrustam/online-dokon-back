from django.contrib import admin
from .models import (
    BotUser, UserAddress,
    Order, OrderItem, FavoriteProduct
)


class UserAddressInline(admin.TabularInline):
    model = UserAddress
    extra = 0
    readonly_fields = ('created_at',)



@admin.register(BotUser)
class BotUserAdmin(admin.ModelAdmin):
    list_display = ('id', 'phone_number', 'telegram_username', 'user_roles', 'language', 'created_at')
    list_filter = ('user_roles', 'language', 'created_at')
    search_fields = ('phone_number', 'telegram_username', 'first_name', 'last_name')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    autocomplete_fields = ('active_shop',)


@admin.register(UserAddress)
class UserAddressAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'full_address', 'created_at')
    search_fields = ('full_address', )
    autocomplete_fields = ('user',)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'quantity', 'price')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'status', 'total_price', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__phone_number',)
    inlines = [OrderItemInline]
    autocomplete_fields = ('user', 'address')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'quantity', 'price')
    search_fields = ('product__title',)
    autocomplete_fields = ('order', 'product')





@admin.register(FavoriteProduct)
class FavoriteProductAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'added_at')
    search_fields = ('user__phone_number', 'product__title')
    autocomplete_fields = ('user', 'product')
    ordering = ('-added_at',)
