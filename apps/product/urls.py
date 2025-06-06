# urls.py
from django.urls import path
from .views import ProductListAPIView, ProductDetailView, CreateBasketAPIView, DeleteBasketAPIView, \
    FavoriteProductAPIView, CreateOrderAPIView, ProductSizeCreateAPIView, ProductColorCreateAPIView, \
    ProductTasteCreateAPIView, ProductVolumeCreateAPIView, ProductTasteListAPIView, ShopColorListAPIView, \
    ShopSizeListAPIView, ProductVolumeListAPIView, ProductCreateAPIView, ProductCategoryCreateAPIView, \
    ProductCategoryListAPIView, FavoriteProductDeleteAPIView, FavoriteListAPIView, BasketListAPIView, \
    ProductColorListAPIView, ProductSizeListAPIView, UpdateBasketQuantityAPIView, ProductImageCreateView, \
    ProductImageDeleteView, ProductVariantCreateView, ProductVariantDeleteView, OrderUserListAPIView, \
    OrderDetailAPIView, OrderListByShopCodeAPIView, OrderShopDetailAPIView, OrderStatusUpdateAPIView

urlpatterns = [
    # path('basket/create/', CreateBasketAPIView.as_view(), name='create-basket'),
    # path('basket/<str:shop_code>/', BasketListAPIView.as_view(), name='basket-list'),
    # path('basket/update/', UpdateBasketQuantityAPIView.as_view(), name='update-basket'),
    # path('basket/<int:pk>/delete/', DeleteBasketAPIView.as_view(), name='delete-basket'),
    path('favorites/', FavoriteProductAPIView.as_view(), name='favorite-product'),
    path('favorites/<str:shop_code>/<int:telegram_id>/', FavoriteListAPIView.as_view(), name='favorite-list'),
    path('favorites/<int:pk>/delete/', FavoriteProductDeleteAPIView.as_view(), name='favorite-product'),
    path('order/create/', CreateOrderAPIView.as_view(), name='create-order'),
    path('orders/list/', OrderUserListAPIView.as_view(), name='user-orders'),
    path('orders/', OrderListByShopCodeAPIView.as_view()),
    path('orders/<int:pk>/', OrderShopDetailAPIView.as_view(), name='order-detail'),
    path('orders/<int:pk>/update-status/', OrderStatusUpdateAPIView.as_view(), name='order-status-update'),
    path('order/detail/<int:pk>/', OrderDetailAPIView.as_view()),
    path('color/create/', ProductColorCreateAPIView.as_view(), name='create-color'),
    path('category/create/', ProductCategoryCreateAPIView.as_view(), name='create-category'),
    path('size/create/', ProductSizeCreateAPIView.as_view(), name='create-size'),
    path('taste/create/', ProductTasteCreateAPIView.as_view(), name='create-taste'),
    path('volume/create/', ProductVolumeCreateAPIView.as_view(), name='create-volume'),
    path('taste/<str:shop_code>/', ProductTasteListAPIView.as_view(), name='list-taste'),
    path('volume/<str:shop_code>/', ProductVolumeListAPIView.as_view(), name='list-volume'),
    path('size/<str:shop_code>/', ShopSizeListAPIView.as_view(), name='list-size'),
    path('sizes/<int:product_id>/', ProductSizeListAPIView.as_view(), name='list-size'),
    path('color/<str:shop_code>/', ShopColorListAPIView.as_view(), name='list-color'),
    path('colors/<int:product_id>/', ProductColorListAPIView.as_view(), name='list-color'),
    path('category/<str:shop_code>/', ProductCategoryListAPIView.as_view(), name='list-category'),
    path('<str:shop_code>/products/', ProductListAPIView.as_view(), name='shop-products'),
    path('<int:pk>/detail/', ProductDetailView.as_view(), name='product-detail'),  # Yoki <str:shop_code>
    path('products/', ProductCreateAPIView.as_view(), name='product-list'),
    path('images/create', ProductImageCreateView.as_view(), name='product-image'),
    path('image/<int:pk>/', ProductImageDeleteView.as_view(), name='product-image'),
    path('variants/create', ProductVariantCreateView.as_view(), name='product-variant'),
    path('variants/<int:pk>/', ProductVariantDeleteView.as_view(), name='product-variant'),
]
