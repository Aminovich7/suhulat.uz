import uuid

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models

from accounts.managers import CustomUserManager


class CustomUser(AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        BUYER = "buyer", "Buyer"
        SELLER = "seller", "Seller"
        BOTH = "both", "Both"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    phone = models.CharField(max_length=20, unique=True)
    email = models.EmailField(blank=True, null=True)
    full_name = models.CharField(max_length=150)
    role = models.CharField(max_length=10, choices=Role.choices)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = CustomUserManager()

    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = ["full_name"]

    class Meta:
        ordering = ["-date_joined"]

    def __str__(self):
        return self.phone

    @property
    def is_buyer(self):
        return self.role in (self.Role.BUYER, self.Role.BOTH)

    @property
    def is_seller(self):
        return self.role in (self.Role.SELLER, self.Role.BOTH)


class SellerProfile(models.Model):
    class SellerType(models.TextChoices):
        SURPLUS = "surplus", "Surplus"
        MAKER = "maker", "Maker"
        WHOLESALE = "wholesale", "Wholesale"

    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="seller_profile",
    )
    seller_name = models.CharField(max_length=200)
    seller_type = models.CharField(max_length=20, choices=SellerType.choices)
    region = models.ForeignKey(
        "listings.Region",
        on_delete=models.PROTECT,
        related_name="seller_profiles",
    )
    district = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_verified = models.BooleanField(default=False)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    total_reviews = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-user__date_joined"]

    def __str__(self):
        return self.seller_name


class BuyerProfile(models.Model):
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="buyer_profile",
    )
    region = models.ForeignKey(
        "listings.Region",
        on_delete=models.PROTECT,
        related_name="buyer_profiles",
    )
    district = models.CharField(max_length=100)
    is_business_buyer = models.BooleanField(default=False)
    company_name = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"Buyer: {self.user.full_name}"
