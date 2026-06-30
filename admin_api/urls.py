from django.urls import include, path
from rest_framework.routers import DefaultRouter

from admin_api.views import (
    AdminListingViewSet,
    AdminReviewViewSet,
    AdminSellerViewSet,
    AdminStatsView,
)

router = DefaultRouter()
router.register("sellers", AdminSellerViewSet, basename="admin-seller")
router.register("listings", AdminListingViewSet, basename="admin-listing")
router.register("reviews", AdminReviewViewSet, basename="admin-review")

urlpatterns = [
    path("stats/", AdminStatsView.as_view(), name="admin-stats"),
    path("", include(router.urls)),
]
