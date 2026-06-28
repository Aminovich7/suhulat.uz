from django.urls import path

from accounts.views import BuyerProfileView, PublicSellerProfileView, SellerProfileView

urlpatterns = [
    path("buyer/me/", BuyerProfileView.as_view(), name="buyer-profile"),
    path("seller/me/", SellerProfileView.as_view(), name="seller-profile"),
    path("sellers/<uuid:user_id>/", PublicSellerProfileView.as_view(), name="public-seller"),
]
