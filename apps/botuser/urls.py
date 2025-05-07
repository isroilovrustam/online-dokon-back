from django.urls import path
from .views import BotUserRegisterView, VerifyCode, BotUserDetailView, GetUserPhoneView, GetVerificationCodeView, \
    SetActiveShopAPIView

urlpatterns = [
    # registration
    path('register/', BotUserRegisterView.as_view(), name='register'),
    path('verify_code/', VerifyCode.as_view(), name='verify_code'),
    path('<int:telegram_id>/', BotUserDetailView.as_view(), name='botuser-detail'),
    path("get-user-phone/<str:telegram_id>/", GetUserPhoneView.as_view()),
    path('verification-code/<str:telegram_id>/', GetVerificationCodeView.as_view(), name='get_verification_code'),
    path("set-active-shop/", SetActiveShopAPIView.as_view(), name="set-active-shop"),
]
