from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from common.test_utils import make_buyer, make_listing, make_seller
from listings.models import Listing
from orders.models import Order


class OrderAPITestCase(APITestCase):
    def setUp(self):
        self.seller = make_seller(phone="+998901111111", verified=True)
        self.buyer = make_buyer(phone="+998902222222")
        self.listing = make_listing(
            self.seller,
            price=Decimal("50.00"),
            quantity=Decimal("10"),
            minimum_order_quantity=Decimal("2"),
        )
        self.client.force_authenticate(self.buyer)

    def test_create_order_decrements_stock(self):
        response = self.client.post(
            reverse("order-list"),
            {
                "listing": str(self.listing.id),
                "quantity": "3",
                "fulfillment_method": "pickup",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.listing.refresh_from_db()
        self.assertEqual(self.listing.quantity_available, Decimal("7"))

    def test_cancel_order_restores_stock(self):
        order = Order.objects.create(
            listing=self.listing,
            buyer=self.buyer,
            seller=self.seller,
            quantity=Decimal("3"),
            unit_price=Decimal("50.00"),
            total_price=Decimal("150.00"),
            fulfillment_method=Order.FulfillmentMethod.PICKUP,
        )
        self.listing.quantity_available = Decimal("7")
        self.listing.save()

        response = self.client.post(reverse("order-cancel", kwargs={"pk": order.pk}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.listing.refresh_from_db()
        self.assertEqual(self.listing.quantity_available, Decimal("10"))
        self.assertEqual(self.listing.status, Listing.Status.ACTIVE)

    def test_cancel_restores_sold_out_listing(self):
        self.listing.quantity_available = Decimal("0")
        self.listing.status = Listing.Status.SOLD_OUT
        self.listing.save()
        order = Order.objects.create(
            listing=self.listing,
            buyer=self.buyer,
            seller=self.seller,
            quantity=Decimal("5"),
            unit_price=Decimal("50.00"),
            total_price=Decimal("250.00"),
            fulfillment_method=Order.FulfillmentMethod.PICKUP,
        )
        response = self.client.post(reverse("order-cancel", kwargs={"pk": order.pk}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.listing.refresh_from_db()
        self.assertEqual(self.listing.quantity_available, Decimal("5"))
        self.assertEqual(self.listing.status, Listing.Status.ACTIVE)

    def test_cannot_order_own_listing(self):
        self.client.force_authenticate(self.seller)
        response = self.client.post(
            reverse("order-list"),
            {
                "listing": str(self.listing.id),
                "quantity": "2",
                "fulfillment_method": "pickup",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cannot_exceed_stock(self):
        response = self.client.post(
            reverse("order-list"),
            {
                "listing": str(self.listing.id),
                "quantity": "100",
                "fulfillment_method": "pickup",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.listing.refresh_from_db()
        self.assertEqual(self.listing.quantity_available, Decimal("10"))

    def test_minimum_order_quantity_enforced(self):
        response = self.client.post(
            reverse("order-list"),
            {
                "listing": str(self.listing.id),
                "quantity": "1",
                "fulfillment_method": "pickup",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
