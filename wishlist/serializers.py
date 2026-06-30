from rest_framework import serializers

from listings.serializers import ListingDetailSerializer
from wishlist.models import Wishlist, WishlistItem


class WishlistItemSerializer(serializers.ModelSerializer):
    listing = ListingDetailSerializer(read_only=True)
    listing_id = serializers.UUIDField(write_only=True)

    class Meta:
        model = WishlistItem
        fields = ["id", "listing", "listing_id", "added_at"]
        read_only_fields = ["id", "added_at"]


class WishlistSerializer(serializers.ModelSerializer):
    items = WishlistItemSerializer(many=True, read_only=True)
    total_items = serializers.IntegerField(read_only=True)

    class Meta:
        model = Wishlist
        fields = ["id", "items", "total_items", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class AddToWishlistSerializer(serializers.Serializer):
    listing_id = serializers.UUIDField()
