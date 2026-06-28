from django.urls import path

from reviews.views import ReviewCreateView, SellerReviewListView

urlpatterns = [
    path("", ReviewCreateView.as_view(), name="review-create"),
    path("seller/<uuid:seller_id>/", SellerReviewListView.as_view(), name="seller-reviews"),
]
