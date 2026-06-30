from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import BuyerProfile
from common.test_utils import make_buyer, make_listing, make_seller
from orders.models import Order
from reviews.models import Review
from reviews.services import update_reviewee_rating


class ReviewRatingTestCase(APITestCase):
    def setUp(self):
        self.seller = make_seller(phone="+998908888888", verified=True)
        self.buyer = make_buyer(phone="+998909999999")
        self.listing = make_listing(self.seller, price=Decimal("20.00"), quantity=Decimal("5"))
        self.order = Order.objects.create(
            listing=self.listing,
            buyer=self.buyer,
            seller=self.seller,
            quantity=Decimal("1"),
            unit_price=Decimal("20.00"),
            total_price=Decimal("20.00"),
            status=Order.Status.COMPLETED,
            fulfillment_method=Order.FulfillmentMethod.PICKUP,
        )

    def test_buyer_review_updates_seller_rating(self):
        self.client.force_authenticate(self.buyer)
        response = self.client.post(
            reverse("review-create"),
            {"order": str(self.order.id), "rating": 5, "comment": "Great"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.seller.seller_profile.refresh_from_db()
        self.assertEqual(self.seller.seller_profile.rating, Decimal("5.00"))
        self.assertEqual(self.seller.seller_profile.total_reviews, 1)

    def test_seller_review_updates_buyer_rating(self):
        self.client.force_authenticate(self.seller)
        response = self.client.post(
            reverse("review-create"),
            {"order": str(self.order.id), "rating": 4, "comment": "Good buyer"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        profile = BuyerProfile.objects.get(user=self.buyer)
        self.assertEqual(profile.rating, Decimal("4.00"))
        self.assertEqual(profile.total_reviews, 1)

    def test_update_reviewee_rating_recalculates(self):
        Review.objects.create(
            order=self.order,
            reviewer=self.buyer,
            reviewee=self.seller,
            rating=3,
            comment="OK",
        )
        update_reviewee_rating(self.seller)
        self.seller.seller_profile.refresh_from_db()
        self.assertEqual(self.seller.seller_profile.total_reviews, 1)
