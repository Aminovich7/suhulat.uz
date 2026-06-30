from rest_framework import serializers

from orders.models import Order
from reviews.models import Review


class ReviewSerializer(serializers.ModelSerializer):
    reviewer_name = serializers.CharField(source="reviewer.full_name", read_only=True)

    class Meta:
        model = Review
        fields = (
            "id",
            "order",
            "reviewer",
            "reviewer_name",
            "reviewee",
            "rating",
            "comment",
            "created_at",
        )
        read_only_fields = ("id", "reviewer", "reviewee", "created_at")


class ReviewCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ("order", "rating", "comment")

    def validate(self, attrs):
        order = attrs["order"]
        user = self.context["request"].user

        if order.status != Order.Status.COMPLETED:
            raise serializers.ValidationError(
                {"order": "Reviews are only allowed after order completion."}
            )
        if user not in (order.buyer, order.seller):
            raise serializers.ValidationError({"order": "Not a party to this order."})
        if hasattr(order, "review"):
            raise serializers.ValidationError({"order": "Review already exists for this order."})

        attrs["reviewer"] = user
        attrs["reviewee"] = order.seller if user == order.buyer else order.buyer
        return attrs

    def create(self, validated_data):
        review = super().create(validated_data)
        from reviews.services import update_reviewee_rating

        update_reviewee_rating(validated_data["reviewee"])
        return review
