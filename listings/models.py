import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class Region(models.Model):
    name_uz = models.CharField(max_length=100)
    name_ru = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)

    class Meta:
        ordering = ["name_uz"]

    def __str__(self):
        return self.name_uz


class Category(models.Model):
    name_uz = models.CharField(max_length=100)
    name_ru = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="children",
    )

    class Meta:
        verbose_name_plural = "categories"
        ordering = ["name_uz"]

    def __str__(self):
        return self.name_uz


class ListingQuerySet(models.QuerySet):
    def public(self):
        return self.filter(status=Listing.Status.ACTIVE)

    def apply_expiry(self):
        now = timezone.now()
        expired = self.filter(
            status=Listing.Status.ACTIVE,
            expires_at__isnull=False,
            expires_at__lt=now,
        )
        count = expired.update(status=Listing.Status.EXPIRED)
        return count


class Listing(models.Model):
    class ListingType(models.TextChoices):
        FIXED = "fixed", "Fixed price"
        NEGOTIABLE = "negotiable", "Negotiable"

    class Unit(models.TextChoices):
        KG = "kg", "Kilogram"
        LITRE = "litre", "Litre"
        PIECE = "piece", "Piece"
        BOX = "box", "Box"
        TON = "ton", "Ton"
        OTHER = "other", "Other"

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        PAUSED = "paused", "Paused"
        SOLD_OUT = "sold_out", "Sold out"
        EXPIRED = "expired", "Expired"
        DELETED = "deleted", "Deleted"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="listings",
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="listings")
    region = models.ForeignKey(Region, on_delete=models.PROTECT, related_name="listings")
    district = models.CharField(max_length=100)
    listing_type = models.CharField(max_length=20, choices=ListingType.choices)
    price = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, default="UZS")
    quantity_available = models.DecimalField(max_digits=12, decimal_places=3)
    unit = models.CharField(max_length=20, choices=Unit.choices)
    minimum_order_quantity = models.DecimalField(
        max_digits=12, decimal_places=3, null=True, blank=True
    )
    is_perishable = models.BooleanField(default=False)
    expires_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PAUSED,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ListingQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "-created_at"]),
            models.Index(fields=["listing_type", "status"]),
            models.Index(fields=["region", "district"]),
        ]

    def __str__(self):
        return self.title


class ListingImage(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="listings/%Y/%m/")
    order = models.PositiveSmallIntegerField(default=1)

    class Meta:
        ordering = ["order"]
        unique_together = [["listing", "order"]]

    def __str__(self):
        return f"{self.listing_id} image #{self.order}"
