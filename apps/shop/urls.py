from django.urls import path
from .views import ShopListAPIView, ShopDetailAPIView, ShopAddressDeleteAPIView, ShopByCodeCheckAPIView, \
    BasketCreateView, BasketListView, BasketUpdateView

urlpatterns = [
    path("by-code/<str:shop_code>/", ShopByCodeCheckAPIView.as_view(), name="shop-by-code"),
    path('list/', ShopListAPIView.as_view(), name="shop-list"),
    path('detail/<str:shop_code>/', ShopDetailAPIView.as_view(), name="shop-detail"),
    path('address/<int:pk>/delete/', ShopAddressDeleteAPIView.as_view(), name='shop-address-delete'),
    path('basket/', BasketCreateView.as_view(), name="basket-create"),
    path('basket/<int:telegram_id>/<str:shop_code>/', BasketListView.as_view(), name="basket-list"),
    path('basket/<int:basket_id>/', BasketUpdateView.as_view(), name="basket-update"),
]
