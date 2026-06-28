from decimal import Decimal

from django.db import transaction
from rest_framework import serializers

from listings.models import Listing
from orders.models import Order


class OrderSerializer(serializers.ModelSerializer):
    listing_title = serializers.CharField(source="listing.title", read_only=True)

    class Meta:
        model = Order
        fields = (
            "id",
            "listing",
            "listing_title",
            "buyer",
            "seller",
            "quantity",
            "unit_price",
            "total_price",
            "status",
            "fulfillment_method",
            "delivery_address",
            "buyer_note",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "buyer",
            "seller",
            "unit_price",
            "total_price",
            "status",
            "created_at",
            "updated_at",
        )


class OrderCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = (
            "listing",
            "quantity",
            "fulfillment_method",
            "delivery_address",
            "buyer_note",
        )

    def validate(self, attrs):
        listing = attrs["listing"]
        quantity = attrs["quantity"]
        request = self.context["request"]

        if listing.listing_type != Listing.ListingType.FIXED:
            raise serializers.ValidationError(
                {"listing": "Orders can only be created for fixed-price listings."}
            )
        if listing.status != Listing.Status.ACTIVE:
            raise serializers.ValidationError({"listing": "Listing is not available."})
        if listing.seller_id == request.user.id:
            raise serializers.ValidationError({"listing": "Cannot order your own listing."})
        if listing.price is None:
            raise serializers.ValidationError({"listing": "Listing has no price."})
        if quantity <= 0:
            raise serializers.ValidationError({"quantity": "Quantity must be positive."})
        if quantity > listing.quantity_available:
            raise serializers.ValidationError(
                {"quantity": "Requested quantity exceeds available stock."}
            )
        if listing.minimum_order_quantity and quantity < listing.minimum_order_quantity:
            raise serializers.ValidationError(
                {
                    "quantity": (
                        f"Minimum order quantity is {listing.minimum_order_quantity}."
                    )
                }
            )
        if attrs["fulfillment_method"] == Order.FulfillmentMethod.DELIVERY:
            if not attrs.get("delivery_address", "").strip():
                raise serializers.ValidationError(
                    {"delivery_address": "Required for delivery orders."}
                )

        attrs["_unit_price"] = listing.price
        attrs["_total_price"] = (listing.price * quantity).quantize(Decimal("0.01"))
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        listing = validated_data["listing"]
        request = self.context["request"]
        order = Order.objects.create(
            listing=listing,
            buyer=request.user,
            seller=listing.seller,
            quantity=validated_data["quantity"],
            unit_price=validated_data["_unit_price"],
            total_price=validated_data["_total_price"],
            fulfillment_method=validated_data["fulfillment_method"],
            delivery_address=validated_data.get("delivery_address", ""),
            buyer_note=validated_data.get("buyer_note", ""),
        )
        listing.quantity_available -= validated_data["quantity"]
        if listing.quantity_available <= 0:
            listing.quantity_available = Decimal("0")
            listing.status = Listing.Status.SOLD_OUT
        listing.save(update_fields=["quantity_available", "status", "updated_at"])
        return order


class OrderStatusTransitionSerializer(serializers.Serializer):
    note = serializers.CharField(required=False, allow_blank=True)

    TRANSITIONS = {
        "confirm": (Order.Status.PENDING, Order.Status.CONFIRMED, "seller"),
        "fulfilling": (Order.Status.CONFIRMED, Order.Status.FULFILLING, "seller"),
        "delivered": (Order.Status.FULFILLING, Order.Status.DELIVERED, "seller"),
        "complete": (Order.Status.DELIVERED, Order.Status.COMPLETED, "buyer"),
    }

    def validate(self, attrs):
        order = self.context["order"]
        action = self.context["action"]
        user = self.context["request"].user

        if action == "cancel":
            if order.status not in Order.CANCELLABLE_STATUSES:
                raise serializers.ValidationError("Order cannot be cancelled at this stage.")
            if user not in (order.buyer, order.seller):
                raise serializers.ValidationError("Not a party to this order.")
            return attrs

        transition = self.TRANSITIONS.get(action)
        if not transition:
            raise serializers.ValidationError("Invalid action.")

        expected_from, expected_to, required_role = transition
        if order.status != expected_from:
            raise serializers.ValidationError(
                f"Order must be in '{expected_from}' status for this action."
            )
        if required_role == "seller" and user != order.seller:
            raise serializers.ValidationError("Only the seller can perform this action.")
        if required_role == "buyer" and user != order.buyer:
            raise serializers.ValidationError("Only the buyer can perform this action.")

        attrs["_new_status"] = expected_to
        return attrs

    @transaction.atomic
    def save(self, **kwargs):
        order = self.context["order"]
        action = self.context["action"]
        if action == "cancel":
            order.status = Order.Status.CANCELLED
        else:
            order.status = self.validated_data["_new_status"]
        order.save(update_fields=["status", "updated_at"])
        return order
