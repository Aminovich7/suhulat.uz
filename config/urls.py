from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter

from config.views import AppView
from listings.views import CategoryViewSet, RegionViewSet

catalog_router = DefaultRouter()
catalog_router.register("regions", RegionViewSet, basename="region")
catalog_router.register("categories", CategoryViewSet, basename="category")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("accounts.urls")),
    path("api/profiles/", include("accounts.profile_urls")),
    path("api/listings/", include("listings.urls")),
    path("api/orders/", include("orders.urls")),
    path("api/rfq/", include("rfq.urls")),
    path("api/reviews/", include("reviews.urls")),
    path("api/cart/", include("cart.urls")),
    path("api/wishlist/", include("wishlist.urls")),
    path("api/admin/", include("admin_api.urls")),
    path("api/", include(catalog_router.urls)),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    path("", AppView.as_view(), name="app"),
    re_path(r"^(?!api/|admin/|static/|media/).+$", AppView.as_view()),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
