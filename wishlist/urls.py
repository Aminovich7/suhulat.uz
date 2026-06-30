from django.urls import include, path
from rest_framework.routers import DefaultRouter

from wishlist.views import WishlistViewSet

wishlist_router = DefaultRouter()
wishlist_router.register("", WishlistViewSet, basename="wishlist")

urlpatterns = [
    path("", include(wishlist_router.urls)),
]
