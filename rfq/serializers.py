from decimal import Decimal

from django.conf import settings
from django.db import transaction
from rest_framework import serializers

from listings.models import Listing
from orders.models import Order
from rfq.models import Offer, RFQ


class OfferSerializer(serializers.ModelSerializer):
    class Meta:
        model = Offer
        fields = (
            "id",
            "proposed_by",
            "price",
            "quantity",
            "message",
            "status",
            "created_at",
        )
        read_only_fields = fields


class RFQSerializer(serializers.ModelSerializer):
    offers = OfferSerializer(many=True, read_only=True)
    listing_title = serializers.CharField(source="listing.title", read_only=True)
    seller_id = serializers.UUIDField(source="listing.seller_id", read_only=True)

    class Meta:
        model = RFQ
        fields = (
            "id",
            "listing",
            "listing_title",
            "seller_id",
            "buyer",
            "quantity_requested",
            "proposed_price",
            "message",
            "status",
            "offers",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "buyer", "status", "created_at", "updated_at", "offers")


class RFQCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = RFQ
        fields = ("listing", "quantity_requested", "proposed_price", "message")

    def validate(self, attrs):
        listing = attrs["listing"]
        request = self.context["request"]

        if listing.listing_type != Listing.ListingType.NEGOTIABLE:
            raise serializers.ValidationError(
                {"listing": "RFQ is only for negotiable listings."}
            )
        if listing.status != Listing.Status.ACTIVE:
            raise serializers.ValidationError({"listing": "Listing is not available."})
        if listing.seller_id == request.user.id:
            raise serializers.ValidationError({"listing": "Cannot RFQ your own listing."})
        if attrs["quantity_requested"] <= 0:
            raise serializers.ValidationError({"quantity_requested": "Must be positive."})
        if attrs["quantity_requested"] > listing.quantity_available:
            raise serializers.ValidationError(
                {"quantity_requested": "Exceeds available quantity."}
            )
        return attrs

    def create(self, validated_data):
        validated_data["buyer"] = self.context["request"].user
        return super().create(validated_data)


class OfferCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Offer
        fields = ("price", "quantity", "message")

    def validate(self, attrs):
        rfq = self.context["rfq"]
        request = self.context["request"]
        user = request.user

        if rfq.status not in (RFQ.Status.OPEN, RFQ.Status.COUNTERED):
            raise serializers.ValidationError("RFQ is no longer open for offers.")

        is_buyer = user == rfq.buyer
        is_seller = user == rfq.listing.seller
        if not is_buyer and not is_seller:
            raise serializers.ValidationError("Not a party to this RFQ.")

        if rfq.offer_count >= settings.RFQ_MAX_OFFER_ROUNDS:
            raise serializers.ValidationError(
                f"Maximum {settings.RFQ_MAX_OFFER_ROUNDS} offer rounds reached."
            )

        if attrs["quantity"] <= 0:
            raise serializers.ValidationError({"quantity": "Must be positive."})
        if attrs["price"] <= 0:
            raise serializers.ValidationError({"price": "Must be positive."})

        attrs["_proposed_by"] = (
            Offer.ProposedBy.BUYER if is_buyer else Offer.ProposedBy.SELLER
        )
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        rfq = self.context["rfq"]
        rfq.offers.filter(status=Offer.Status.PENDING).update(status=Offer.Status.SUPERSEDED)
        offer = Offer.objects.create(
            rfq=rfq,
            proposed_by=validated_data.pop("_proposed_by"),
            price=validated_data["price"],
            quantity=validated_data["quantity"],
            message=validated_data.get("message", ""),
        )
        rfq.status = RFQ.Status.COUNTERED
        rfq.save(update_fields=["status", "updated_at"])
        return offer


class RFQActionSerializer(serializers.Serializer):
    @transaction.atomic
    def accept(self, rfq, user):
        if user not in (rfq.buyer, rfq.listing.seller):
            raise serializers.ValidationError("Not a party to this RFQ.")
        if rfq.status not in (RFQ.Status.OPEN, RFQ.Status.COUNTERED):
            raise serializers.ValidationError("RFQ cannot be accepted in current status.")

        latest = rfq.offers.filter(status=Offer.Status.PENDING).order_by("-created_at").first()
        if latest is None and rfq.proposed_price:
            price = rfq.proposed_price
            quantity = rfq.quantity_requested
        elif latest:
            price = latest.price
            quantity = latest.quantity
            latest.status = Offer.Status.ACCEPTED
            latest.save(update_fields=["status"])
            rfq.offers.filter(status=Offer.Status.PENDING).exclude(pk=latest.pk).update(
                status=Offer.Status.REJECTED
            )
        else:
            raise serializers.ValidationError("No offer to accept.")

        listing = rfq.listing
        total_price = (price * quantity).quantize(Decimal("0.01"))

        order = Order.objects.create(
            listing=listing,
            buyer=rfq.buyer,
            seller=listing.seller,
            quantity=quantity,
            unit_price=price,
            total_price=total_price,
            fulfillment_method=Order.FulfillmentMethod.PICKUP,
            buyer_note=rfq.message,
        )

        listing.quantity_available -= quantity
        if listing.quantity_available <= 0:
            listing.quantity_available = Decimal("0")
            listing.status = Listing.Status.SOLD_OUT
        listing.save(update_fields=["quantity_available", "status", "updated_at"])

        rfq.status = RFQ.Status.ACCEPTED
        rfq.save(update_fields=["status", "updated_at"])
        return order

    @transaction.atomic
    def reject(self, rfq, user):
        if user not in (rfq.buyer, rfq.listing.seller):
            raise serializers.ValidationError("Not a party to this RFQ.")
        if rfq.status not in (RFQ.Status.OPEN, RFQ.Status.COUNTERED):
            raise serializers.ValidationError("RFQ cannot be rejected in current status.")

        rfq.offers.filter(status=Offer.Status.PENDING).update(status=Offer.Status.REJECTED)
        rfq.status = RFQ.Status.REJECTED
        rfq.save(update_fields=["status", "updated_at"])
        return rfq
