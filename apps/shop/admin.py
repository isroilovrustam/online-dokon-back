# admin.py
from django.contrib import admin
from .models import (Shop, ShopAddress, Cart, CartItem)


class ShopAddressInline(admin.TabularInline):
    model = ShopAddress
    extra = 1


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0


@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    list_display = ('shop_name', 'owner', 'shop_code', 'is_active', 'shop_type', 'is_subscription_active')
    list_filter = ('shop_type', 'is_active')
    search_fields = ('shop_name', 'shop_code', 'owner__user_id')
    prepopulated_fields = {"shop_code": ("shop_name",)}
    inlines = [ShopAddressInline]
    save_on_top = True
    autocomplete_fields = ['owner']


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'shop', 'total_price', 'created_at')
    inlines = [CartItemInline]
    search_fields = ('user__user_id', 'shop__shop_name')
    readonly_fields = ('total_price',)


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('cart', 'product', 'quantity', 'price')
    autocomplete_fields = ['product', 'cart']
