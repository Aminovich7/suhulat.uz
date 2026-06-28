from django.conf import settings
from django.db import models


class RFQ(models.Model):
    class Status(models.TextChoices):
        OPEN = "open", "Open"
        COUNTERED = "countered", "Countered"
        ACCEPTED = "accepted", "Accepted"
        REJECTED = "rejected", "Rejected"
        EXPIRED = "expired", "Expired"

    listing = models.ForeignKey(
        "listings.Listing",
        on_delete=models.CASCADE,
        related_name="rfqs",
    )
    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="rfqs",
    )
    quantity_requested = models.DecimalField(max_digits=12, decimal_places=3)
    proposed_price = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "RFQ"
        verbose_name_plural = "RFQs"

    def __str__(self):
        return f"RFQ #{self.pk} — {self.listing.title}"

    @property
    def offer_count(self):
        return self.offers.count()


class Offer(models.Model):
    class ProposedBy(models.TextChoices):
        BUYER = "buyer", "Buyer"
        SELLER = "seller", "Seller"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACCEPTED = "accepted", "Accepted"
        REJECTED = "rejected", "Rejected"
        SUPERSEDED = "superseded", "Superseded"

    rfq = models.ForeignKey(RFQ, on_delete=models.CASCADE, related_name="offers")
    proposed_by = models.CharField(max_length=10, choices=ProposedBy.choices)
    price = models.DecimalField(max_digits=14, decimal_places=2)
    quantity = models.DecimalField(max_digits=12, decimal_places=3)
    message = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Offer #{self.pk} on RFQ #{self.rfq_id}"
