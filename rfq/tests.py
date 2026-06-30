from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from common.test_utils import make_buyer, make_listing, make_seller
from listings.models import Listing
from orders.models import Order
from rfq.models import RFQ


class RFQAPITestCase(APITestCase):
    def setUp(self):
        self.seller = make_seller(phone="+998903333333", verified=True)
        self.buyer = make_buyer(phone="+998904444444")
        self.listing = make_listing(
            self.seller,
            listing_type=Listing.ListingType.NEGOTIABLE,
            price=None,
            quantity=Decimal("100"),
        )
        self.client.force_authenticate(self.buyer)

    def test_create_rfq(self):
        response = self.client.post(
            reverse("rfq-list"),
            {
                "listing": str(self.listing.id),
                "quantity_requested": "50",
                "proposed_price": "40.00",
                "message": "Bulk order please",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(RFQ.objects.count(), 1)

    def test_accept_rfq_creates_order_and_decrements_stock(self):
        rfq = RFQ.objects.create(
            listing=self.listing,
            buyer=self.buyer,
            quantity_requested=Decimal("20"),
            proposed_price=Decimal("45.00"),
            message="Offer",
        )
        self.client.force_authenticate(self.seller)
        response = self.client.post(reverse("rfq-accept", kwargs={"pk": rfq.pk}))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.listing.refresh_from_db()
        self.assertEqual(self.listing.quantity_available, Decimal("80"))
        self.assertEqual(Order.objects.count(), 1)

    def test_accept_rfq_fails_when_stock_insufficient(self):
        rfq = RFQ.objects.create(
            listing=self.listing,
            buyer=self.buyer,
            quantity_requested=Decimal("150"),
            proposed_price=Decimal("45.00"),
            message="Too much",
        )
        self.client.force_authenticate(self.seller)
        response = self.client.post(reverse("rfq-accept", kwargs={"pk": rfq.pk}))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.listing.refresh_from_db()
        self.assertEqual(self.listing.quantity_available, Decimal("100"))
