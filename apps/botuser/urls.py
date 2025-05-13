from django.urls import path
from .views import BotUserRegisterView, BotUserDetailView, SetActiveShopAPIView, AddressDetailView

urlpatterns = [
    # registration
    path('register/', BotUserRegisterView.as_view(), name='register'),
    path('<int:telegram_id>/', BotUserDetailView.as_view(), name='botuser-detail'),
    path("set-active-shop/", SetActiveShopAPIView.as_view(), name="set-active-shop"),
    path("address/delete/<int:pk>", AddressDetailView.as_view(), name="delete-address"),
]
