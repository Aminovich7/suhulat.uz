import uuid

from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError

from listings.models import Listing


class Cart(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="cart",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        indexes = [
            models.Index(fields=["user"]),
        ]

    def __str__(self):
        return f"Cart: {self.user.phone}"

    @property
    def total_items(self):
        return self.items.aggregate(
            total=models.Sum("quantity")
        )["total"] or 0

    @property
    def total_price(self):
        from django.db.models import F, Sum, DecimalField
        return self.items.aggregate(
            total=Sum(
                F("quantity") * F("listing__price"),
                output_field=DecimalField(),
            )
        )["total"] or 0


class CartItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name="items",
    )
    listing = models.ForeignKey(
        Listing,
        on_delete=models.CASCADE,
        related_name="cart_items",
    )
    quantity = models.DecimalField(max_digits=12, decimal_places=3)
    added_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-added_at"]
        unique_together = [["cart", "listing"]]
        indexes = [
            models.Index(fields=["cart", "listing"]),
        ]

    def __str__(self):
        return f"{self.listing.title} x {self.quantity}"

    def clean(self):
        if self.quantity <= 0:
            raise ValidationError({"quantity": "Quantity must be greater than 0."})

        if self.quantity > self.listing.quantity_available:
            raise ValidationError(
                {"quantity": f"Available quantity: {self.listing.quantity_available}"}
            )

        if self.listing.status != Listing.Status.ACTIVE:
            raise ValidationError(
                {"listing": "This listing is no longer available."}
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
