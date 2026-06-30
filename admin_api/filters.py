import django_filters

from accounts.models import SellerProfile
from listings.models import Listing
from reviews.models import Review


class AdminSellerFilter(django_filters.FilterSet):
    is_verified = django_filters.BooleanFilter(field_name="is_verified")

    class Meta:
        model = SellerProfile
        fields = ("is_verified", "seller_type", "region")


class AdminListingFilter(django_filters.FilterSet):
    status = django_filters.ChoiceFilter(choices=Listing.Status.choices)
    listing_type = django_filters.ChoiceFilter(choices=Listing.ListingType.choices)
    region = django_filters.NumberFilter(field_name="region_id")

    class Meta:
        model = Listing
        fields = ("status", "listing_type", "region")


class AdminReviewFilter(django_filters.FilterSet):
    rating = django_filters.NumberFilter()
    reviewee = django_filters.UUIDFilter(field_name="reviewee_id")

    class Meta:
        model = Review
        fields = ("rating", "reviewee")
