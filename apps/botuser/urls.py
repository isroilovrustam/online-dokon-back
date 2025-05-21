from django.urls import path
from .views import BotUserRegisterView, BotUserDetailView, SetActiveShopAPIView, AddressDetailView, ReklamaListView, \
    AddressCreateByTelegramView, ReceptionMethodListCreateAPIView, ReceptionMethodDetailAPIView

urlpatterns = [
    # registration
    path('register/', BotUserRegisterView.as_view(), name='register'),
    path('<int:telegram_id>/', BotUserDetailView.as_view(), name='botuser-detail'),
    path("set-active-shop/", SetActiveShopAPIView.as_view(), name="set-active-shop"),
    path("address/delete/<int:pk>", AddressDetailView.as_view(), name="delete-address"),
    path("address/create/<int:telegram_id>", AddressCreateByTelegramView.as_view(), name="create-address-by-telegram"),
    path("reklama/<str:shop_code>", ReklamaListView.as_view(), name="reklama-list"),
    path('reception-method/', ReceptionMethodListCreateAPIView.as_view),
    path('reception-method/<int:pk>/', ReceptionMethodDetailAPIView.as_view),
]
