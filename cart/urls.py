from django.urls import include, path
from rest_framework.routers import DefaultRouter

from cart.views import CartViewSet

cart_router = DefaultRouter()
cart_router.register("", CartViewSet, basename="cart")

urlpatterns = [
    path("", include(cart_router.urls)),
]
