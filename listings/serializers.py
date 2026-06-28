from django.conf import settings
from rest_framework import serializers

from listings.models import Category, Listing, ListingImage, Region


class RegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = ("id", "name_uz", "name_ru", "code")


class CategorySerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ("id", "name_uz", "name_ru", "slug", "parent", "children")

    def get_children(self, obj):
        if self.context.get("flat"):
            return []
        children = obj.children.all()
        return CategorySerializer(children, many=True, context={"flat": True}).data


class ListingImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ListingImage
        fields = ("id", "image", "order")
        read_only_fields = ("id",)


class ListingListSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    region = RegionSerializer(read_only=True)
    seller_name = serializers.CharField(
        source="seller.seller_profile.seller_name", read_only=True, default=""
    )
    primary_image = serializers.SerializerMethodField()

    class Meta:
        model = Listing
        fields = (
            "id",
            "title",
            "listing_type",
            "price",
            "currency",
            "quantity_available",
            "unit",
            "region",
            "district",
            "category",
            "seller_name",
            "status",
            "is_perishable",
            "expires_at",
            "created_at",
            "primary_image",
        )

    def get_primary_image(self, obj):
        image = obj.images.first()
        if image and image.image:
            request = self.context.get("request")
            url = image.image.url
            return request.build_absolute_uri(url) if request else url
        return None


class ListingDetailSerializer(ListingListSerializer):
    images = ListingImageSerializer(many=True, read_only=True)
    seller_id = serializers.UUIDField(source="seller.id", read_only=True)

    class Meta(ListingListSerializer.Meta):
        fields = ListingListSerializer.Meta.fields + (
            "description",
            "minimum_order_quantity",
            "seller_id",
            "images",
            "updated_at",
        )


class ListingWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Listing
        fields = (
            "title",
            "description",
            "category",
            "region",
            "district",
            "listing_type",
            "price",
            "currency",
            "quantity_available",
            "unit",
            "minimum_order_quantity",
            "is_perishable",
            "expires_at",
            "status",
        )

    def validate(self, attrs):
        listing_type = attrs.get(
            "listing_type",
            getattr(self.instance, "listing_type", None),
        )
        price = attrs.get("price", getattr(self.instance, "price", None))

        if listing_type == Listing.ListingType.FIXED and price is None:
            raise serializers.ValidationError(
                {"price": "Price is required for fixed-price listings."}
            )
        if listing_type == Listing.ListingType.NEGOTIABLE:
            attrs["price"] = None

        status_value = attrs.get("status")
        if status_value == Listing.Status.ACTIVE:
            user = self.context["request"].user
            profile = getattr(user, "seller_profile", None)
            if not profile or not profile.is_verified:
                raise serializers.ValidationError(
                    {"status": "Seller must be verified to publish active listings."}
                )

        return attrs

    def create(self, validated_data):
        validated_data["seller"] = self.context["request"].user
        return super().create(validated_data)


class ListingImageUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = ListingImage
        fields = ("image", "order")

    def validate(self, attrs):
        listing = self.context["listing"]
        order = attrs.get("order", 1)
        if listing.images.count() >= settings.LISTING_MAX_IMAGES:
            raise serializers.ValidationError(
                f"Maximum {settings.LISTING_MAX_IMAGES} images per listing."
            )
        if order < 1 or order > settings.LISTING_MAX_IMAGES:
            raise serializers.ValidationError(
                f"Image order must be between 1 and {settings.LISTING_MAX_IMAGES}."
            )
        if listing.images.filter(order=order).exists():
            raise serializers.ValidationError(f"Order {order} is already taken.")
        return attrs
