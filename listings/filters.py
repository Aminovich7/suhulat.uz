from django_filters import rest_framework as filters

from listings.models import Listing


class ListingFilter(filters.FilterSet):
    category = filters.NumberFilter(field_name="category_id")
    region = filters.NumberFilter(field_name="region_id")
    district = filters.CharFilter(field_name="district", lookup_expr="icontains")
    listing_type = filters.CharFilter(field_name="listing_type")
    seller_type = filters.CharFilter(field_name="seller__seller_profile__seller_type")
    price_min = filters.NumberFilter(field_name="price", lookup_expr="gte")
    price_max = filters.NumberFilter(field_name="price", lookup_expr="lte")
    negotiable = filters.BooleanFilter(method="filter_negotiable")
    seller = filters.UUIDFilter(field_name="seller_id")

    class Meta:
        model = Listing
        fields = [
            "category",
            "region",
            "district",
            "listing_type",
            "seller_type",
            "price_min",
            "price_max",
            "negotiable",
            "seller",
        ]

    def filter_negotiable(self, queryset, name, value):
        if value:
            return queryset.filter(listing_type=Listing.ListingType.NEGOTIABLE)
        return queryset.filter(listing_type=Listing.ListingType.FIXED)
