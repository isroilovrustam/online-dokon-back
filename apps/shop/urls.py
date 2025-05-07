from django.urls import path
from .views import ShopByCodeCheckAPIView, ShopListAPIView, ShopDetailAPIView

urlpatterns = [
    path("by-code/<str:shop_code>/", ShopByCodeCheckAPIView.as_view(), name="shop-by-code"),
    path('list/', ShopListAPIView.as_view(), name="shop-list"),
    path('detail/<str:shop_code>/', ShopDetailAPIView.as_view(), name="shop-detail"),
]
