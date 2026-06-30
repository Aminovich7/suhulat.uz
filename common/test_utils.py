from decimal import Decimal

from django.contrib.auth import get_user_model

from accounts.models import BuyerProfile, SellerProfile
from listings.models import Category, Listing, Region

User = get_user_model()


def make_region(code="TST", name_uz="Test viloyat", name_ru="Test"):
    return Region.objects.create(name_uz=name_uz, name_ru=name_ru, code=code)


def make_category(slug="test-cat", name_uz="Test", name_ru="Test"):
    return Category.objects.create(name_uz=name_uz, name_ru=name_ru, slug=slug)


def make_buyer(phone="+998901234567", password="testpass123", **kwargs):
    region = kwargs.pop("region", None) or make_region(code=f"B{phone[-4:]}")
    user = User.objects.create_user(
        phone=phone,
        password=password,
        full_name=kwargs.pop("full_name", "Test Buyer"),
        role=User.Role.BUYER,
        **kwargs,
    )
    BuyerProfile.objects.create(
        user=user,
        region=region,
        district="Test district",
    )
    return user


def make_seller(
    phone="+998901234568",
    password="testpass123",
    verified=True,
    seller_type=SellerProfile.SellerType.SURPLUS,
    **kwargs,
):
    region = kwargs.pop("region", None) or make_region(code=f"S{phone[-4:]}")
    user = User.objects.create_user(
        phone=phone,
        password=password,
        full_name=kwargs.pop("full_name", "Test Seller"),
        role=User.Role.SELLER,
        **kwargs,
    )
    SellerProfile.objects.create(
        user=user,
        seller_name=kwargs.pop("seller_name", "Test Seller Shop"),
        seller_type=seller_type,
        region=region,
        district="Test district",
        is_verified=verified,
    )
    return user


def make_listing(
    seller,
    listing_type=Listing.ListingType.FIXED,
    price=Decimal("100.00"),
    quantity=Decimal("10"),
    status=Listing.Status.ACTIVE,
    **kwargs,
):
    region = kwargs.pop("region", None) or seller.seller_profile.region
    category = kwargs.pop("category", None) or make_category(
        slug=f"cat-{Listing.objects.count()}"
    )
    return Listing.objects.create(
        seller=seller,
        title=kwargs.pop("title", "Test listing"),
        description=kwargs.pop("description", "Test description"),
        category=category,
        region=region,
        district=kwargs.pop("district", "Test district"),
        listing_type=listing_type,
        price=price if listing_type == Listing.ListingType.FIXED else None,
        quantity_available=quantity,
        unit=kwargs.pop("unit", Listing.Unit.KG),
        minimum_order_quantity=kwargs.pop("minimum_order_quantity", None),
        status=status,
        **kwargs,
    )
