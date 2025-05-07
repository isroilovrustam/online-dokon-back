from django.urls import path, include

urlpatterns = [
    path("botuser/", include('botuser.urls')),
    path("shop/", include('shop.urls')),
    path("product/", include('product.urls')),
]