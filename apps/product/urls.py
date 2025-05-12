# urls.py
from django.urls import path
from .views import ProductListAPIView, ProductDetailView, CreateBasketAPIView, DeleteBasketAPIView, \
    FavoriteProductAPIView, CreateOrderAPIView

urlpatterns = [
    path('basket/create/', CreateBasketAPIView.as_view(), name='create-basket'),
    path('basket/delete/', DeleteBasketAPIView.as_view(), name='delete-basket'),
    path('favorites/', FavoriteProductAPIView.as_view(), name='favorite-product'),
    path('order/create/', CreateOrderAPIView.as_view(), name='create-order'),

    path('<str:shop_code>/products/', ProductListAPIView.as_view(), name='shop-products'),
    path('api/v1/product/<int:pk>/detail/', ProductDetailView.as_view(), name='product-detail'),  # Yoki <str:shop_code>
]
