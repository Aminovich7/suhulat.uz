from decimal import Decimal

from django.db.models import Avg, Count

from accounts.models import BuyerProfile, SellerProfile
from reviews.models import Review


def update_reviewee_rating(user) -> None:
    """Recalculate rating aggregates for seller and/or buyer profile of reviewee."""
    stats = Review.objects.filter(reviewee=user).aggregate(
        avg=Avg("rating"),
        count=Count("id"),
    )
    rating = Decimal(str(round(stats["avg"] or 0, 2)))
    total = stats["count"]

    seller_profile = getattr(user, "seller_profile", None)
    if seller_profile is not None:
        seller_profile.rating = rating
        seller_profile.total_reviews = total
        seller_profile.save(update_fields=["rating", "total_reviews"])

    buyer_profile = getattr(user, "buyer_profile", None)
    if buyer_profile is not None:
        buyer_profile.rating = rating
        buyer_profile.total_reviews = total
        buyer_profile.save(update_fields=["rating", "total_reviews"])


def update_seller_rating(user) -> None:
    """Backward-compatible alias."""
    update_reviewee_rating(user)
