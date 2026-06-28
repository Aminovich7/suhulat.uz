from django.urls import include, path
from rest_framework.routers import DefaultRouter

from rfq.views import RFQViewSet

router = DefaultRouter()
router.register("", RFQViewSet, basename="rfq")

urlpatterns = [
    path("", include(router.urls)),
]
