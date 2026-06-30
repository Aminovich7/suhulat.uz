from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import SellerProfile
from common.test_utils import make_buyer, make_listing, make_seller
from listings.models import Listing
from listings.serializers import ListingWriteSerializer


class ListingValidationTestCase(APITestCase):
    def setUp(self):
        self.seller = make_seller(phone="+998905555555", verified=False)
        self.region = self.seller.seller_profile.region
        self.category = make_listing(self.seller).category

    def test_perishable_requires_expires_at(self):
        serializer = ListingWriteSerializer(
            data={
                "title": "Tomatoes",
                "description": "Fresh",
                "category": self.category.id,
                "region": self.region.id,
                "district": "Test",
                "listing_type": "fixed",
                "price": "10.00",
                "quantity_available": "5",
                "unit": "kg",
                "is_perishable": True,
                "status": "paused",
            },
            context={"request": type("R", (), {"user": self.seller})()},
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("expires_at", serializer.errors)

    def test_unverified_seller_can_create_paused_listing(self):
        self.client.force_authenticate(self.seller)
        response = self.client.post(
            reverse("listing-list"),
            {
                "title": "Draft listing",
                "description": "Waiting verification",
                "category": self.category.id,
                "region": self.region.id,
                "district": "Test",
                "listing_type": "fixed",
                "price": "25.00",
                "quantity_available": "3",
                "unit": "kg",
                "status": "paused",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        listing = Listing.objects.get(pk=response.data["id"])
        self.assertEqual(listing.status, Listing.Status.PAUSED)


class CartAPITestCase(APITestCase):
    def setUp(self):
        self.seller = make_seller(
            phone="+998906666666",
            verified=True,
            seller_type=SellerProfile.SellerType.WHOLESALE,
        )
        self.buyer = make_buyer(phone="+998907777777")
        self.listing = make_listing(
            self.seller,
            price=Decimal("30.00"),
            quantity=Decimal("20"),
            minimum_order_quantity=Decimal("5"),
        )
        self.negotiable = make_listing(
            self.seller,
            title="Negotiable bulk",
            listing_type=Listing.ListingType.NEGOTIABLE,
            price=None,
            quantity=Decimal("50"),
        )
        self.client.force_authenticate(self.buyer)

    def test_add_fixed_listing_to_cart(self):
        response = self.client.post(
            reverse("cart-add-item"),
            {"listing_id": str(self.listing.id), "quantity": "5"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_reject_negotiable_listing_in_cart(self):
        response = self.client.post(
            reverse("cart-add-item"),
            {"listing_id": str(self.negotiable.id), "quantity": "5"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reject_own_listing_in_cart(self):
        self.client.force_authenticate(self.seller)
        response = self.client.post(
            reverse("cart-add-item"),
            {"listing_id": str(self.listing.id), "quantity": "5"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_minimum_order_quantity_on_add(self):
        response = self.client.post(
            reverse("cart-add-item"),
            {"listing_id": str(self.listing.id), "quantity": "2"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_minimum_order_quantity_on_update(self):
        add_resp = self.client.post(
            reverse("cart-add-item"),
            {"listing_id": str(self.listing.id), "quantity": "5"},
            format="json",
        )
        item_id = add_resp.data["id"]
        response = self.client.post(
            reverse("cart-update-item"),
            {"item_id": item_id, "quantity": "2"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
