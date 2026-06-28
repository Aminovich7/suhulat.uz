from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from accounts.jwt import PhoneTokenObtainPairSerializer
from accounts.views import (
    BothRegisterView,
    BuyerRegisterView,
    MeView,
    SellerRegisterView,
)


class CustomLoginView(TokenObtainPairView):
    serializer_class = PhoneTokenObtainPairSerializer


urlpatterns = [
    path("register/buyer/", BuyerRegisterView.as_view(), name="register-buyer"),
    path("register/seller/", SellerRegisterView.as_view(), name="register-seller"),
    path("register/both/", BothRegisterView.as_view(), name="register-both"),
    path("login/", CustomLoginView.as_view(), name="login"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("me/", MeView.as_view(), name="me"),
]
