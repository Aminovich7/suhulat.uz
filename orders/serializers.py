from decimal import Decimal

from django.db import transaction
from rest_framework import serializers

from listings.models import Listing
from orders.models import Order


def validate_listing_order(listing, quantity, user, fulfillment_method, delivery_address=""):
    """Shared validation for order creation against a listing row."""
    errors = {}
    if listing.listing_type != Listing.ListingType.FIXED:
        errors["listing"] = "Orders can only be created for fixed-price listings."
    elif listing.status != Listing.Status.ACTIVE:
        errors["listing"] = "Listing is not available."
    elif listing.seller_id == user.id:
        errors["listing"] = "Cannot order your own listing."
    elif listing.price is None:
        errors["listing"] = "Listing has no price."
    elif quantity <= 0:
        errors["quantity"] = "Quantity must be positive."
    elif quantity > listing.quantity_available:
        errors["quantity"] = "Requested quantity exceeds available stock."
    elif listing.minimum_order_quantity and quantity < listing.minimum_order_quantity:
        errors["quantity"] = f"Minimum order quantity is {listing.minimum_order_quantity}."
    if fulfillment_method == Order.FulfillmentMethod.DELIVERY:
        if not (delivery_address or "").strip():
            errors["delivery_address"] = "Required for delivery orders."
    if errors:
        raise serializers.ValidationError(errors)


def restore_listing_stock(listing, quantity):
    listing.quantity_available += quantity
    if listing.status == Listing.Status.SOLD_OUT and listing.quantity_available > 0:
        listing.status = Listing.Status.ACTIVE
    listing.save(update_fields=["quantity_available", "status", "updated_at"])


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
        validate_listing_order(
            listing,
            attrs["quantity"],
            self.context["request"].user,
            attrs["fulfillment_method"],
            attrs.get("delivery_address", ""),
        )
        attrs["_unit_price"] = listing.price
        attrs["_total_price"] = (listing.price * attrs["quantity"]).quantize(Decimal("0.01"))
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        listing = Listing.objects.select_for_update().get(
            pk=validated_data["listing"].pk
        )
        quantity = validated_data["quantity"]
        request = self.context["request"]
        validate_listing_order(
            listing,
            quantity,
            request.user,
            validated_data["fulfillment_method"],
            validated_data.get("delivery_address", ""),
        )
        unit_price = listing.price
        order = Order.objects.create(
            listing=listing,
            buyer=request.user,
            seller=listing.seller,
            quantity=quantity,
            unit_price=unit_price,
            total_price=(unit_price * quantity).quantize(Decimal("0.01")),
            fulfillment_method=validated_data["fulfillment_method"],
            delivery_address=validated_data.get("delivery_address", ""),
            buyer_note=validated_data.get("buyer_note", ""),
        )
        listing.quantity_available -= quantity
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
            listing = Listing.objects.select_for_update().get(pk=order.listing_id)
            restore_listing_stock(listing, order.quantity)
            order.status = Order.Status.CANCELLED
        else:
            order.status = self.validated_data["_new_status"]
        order.save(update_fields=["status", "updated_at"])
        return order
