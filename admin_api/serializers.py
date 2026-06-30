from rest_framework import serializers

from accounts.models import SellerProfile
from accounts.serializers import RegionBriefSerializer
from listings.models import Listing
from listings.serializers import ListingListSerializer
from reviews.models import Review


class AdminStatsSerializer(serializers.Serializer):
    sellers_pending = serializers.IntegerField()
    sellers_total = serializers.IntegerField()
    listings_total = serializers.IntegerField()
    listings_by_status = serializers.DictField(child=serializers.IntegerField())
    reviews_total = serializers.IntegerField()


class AdminSellerSerializer(serializers.ModelSerializer):
    user_id = serializers.UUIDField(source="user.id", read_only=True)
    phone = serializers.CharField(source="user.phone", read_only=True)
    full_name = serializers.CharField(source="user.full_name", read_only=True)
    is_active = serializers.BooleanField(source="user.is_active", read_only=True)
    date_joined = serializers.DateTimeField(source="user.date_joined", read_only=True)
    region = RegionBriefSerializer(read_only=True)

    class Meta:
        model = SellerProfile
        fields = (
            "user_id",
            "phone",
            "full_name",
            "seller_name",
            "seller_type",
            "region",
            "district",
            "description",
            "is_verified",
            "is_active",
            "rating",
            "total_reviews",
            "date_joined",
        )


class AdminListingSerializer(ListingListSerializer):
    seller_id = serializers.UUIDField(source="seller.id", read_only=True)
    seller_phone = serializers.CharField(source="seller.phone", read_only=True)

    class Meta(ListingListSerializer.Meta):
        fields = ListingListSerializer.Meta.fields + ("seller_id", "seller_phone")


class AdminReviewSerializer(serializers.ModelSerializer):
    reviewer_name = serializers.CharField(source="reviewer.full_name", read_only=True)
    reviewee_name = serializers.CharField(source="reviewee.full_name", read_only=True)
    listing_title = serializers.CharField(source="order.listing.title", read_only=True)

    class Meta:
        model = Review
        fields = (
            "id",
            "order",
            "listing_title",
            "reviewer",
            "reviewer_name",
            "reviewee",
            "reviewee_name",
            "rating",
            "comment",
            "created_at",
        )


class ListingModerateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Listing.Status.choices)

    def validate_status(self, value):
        allowed = {
            Listing.Status.ACTIVE,
            Listing.Status.PAUSED,
            Listing.Status.DELETED,
        }
        if value not in allowed:
            raise serializers.ValidationError(
                "Admin can only set status to active, paused, or deleted."
            )
        return value


class SellerRejectSerializer(serializers.Serializer):
    deactivate_user = serializers.BooleanField(default=False)
