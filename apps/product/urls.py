# urls.py
from django.urls import path
from .views import ProductListAPIView, ProductDetailView

urlpatterns = [
    path('<str:shop_code>/products/', ProductListAPIView.as_view(), name='shop-products'),
    path('api/v1/product/<int:pk>/detail/', ProductDetailView.as_view(), name='product-detail'),  # Yoki <str:shop_code>
]
