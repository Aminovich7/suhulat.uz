from django.contrib.auth import get_user_model
from rest_framework import serializers

from accounts.models import BuyerProfile, SellerProfile
from listings.models import Region

User = get_user_model()


class RegionBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = ("id", "name_uz", "name_ru", "code")


class BuyerProfileSerializer(serializers.ModelSerializer):
    region = RegionBriefSerializer(read_only=True)
    region_id = serializers.PrimaryKeyRelatedField(
        queryset=Region.objects.all(), source="region", write_only=True
    )

    class Meta:
        model = BuyerProfile
        fields = (
            "region",
            "region_id",
            "district",
            "is_business_buyer",
            "company_name",
        )
        read_only_fields = ("region",)


class SellerProfileSerializer(serializers.ModelSerializer):
    region = RegionBriefSerializer(read_only=True)
    region_id = serializers.PrimaryKeyRelatedField(
        queryset=Region.objects.all(), source="region", write_only=True
    )

    class Meta:
        model = SellerProfile
        fields = (
            "seller_name",
            "seller_type",
            "region",
            "region_id",
            "district",
            "description",
            "is_verified",
            "rating",
            "total_reviews",
        )
        read_only_fields = ("is_verified", "rating", "total_reviews", "region")


class UserSerializer(serializers.ModelSerializer):
    buyer_profile = BuyerProfileSerializer(read_only=True)
    seller_profile = SellerProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "phone",
            "email",
            "full_name",
            "role",
            "date_joined",
            "buyer_profile",
            "seller_profile",
        )
        read_only_fields = fields


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("email", "full_name")


class BuyerRegisterSerializer(serializers.Serializer):
    phone = serializers.RegexField(regex=r"^\+998\d{9}$", max_length=20)
    password = serializers.CharField(write_only=True, min_length=8)
    full_name = serializers.CharField(max_length=150)
    email = serializers.EmailField(required=False, allow_blank=True)
    region_id = serializers.PrimaryKeyRelatedField(queryset=Region.objects.all(), source="region")
    district = serializers.CharField(max_length=100)
    is_business_buyer = serializers.BooleanField(default=False)
    company_name = serializers.CharField(max_length=200, required=False, allow_blank=True)

    def validate_phone(self, value):
        if User.objects.filter(phone=value).exists():
            raise serializers.ValidationError("A user with this phone already exists.")
        return value

    def create(self, validated_data):
        region = validated_data.pop("region")
        profile_data = {
            "region": region,
            "district": validated_data.pop("district"),
            "is_business_buyer": validated_data.pop("is_business_buyer", False),
            "company_name": validated_data.pop("company_name", ""),
        }
        email = validated_data.pop("email", "") or None
        user = User.objects.create_user(
            role=User.Role.BUYER,
            email=email,
            **validated_data,
        )
        BuyerProfile.objects.create(user=user, **profile_data)
        return user


class SellerRegisterSerializer(serializers.Serializer):
    phone = serializers.RegexField(regex=r"^\+998\d{9}$", max_length=20)
    password = serializers.CharField(write_only=True, min_length=8)
    full_name = serializers.CharField(max_length=150)
    email = serializers.EmailField(required=False, allow_blank=True)
    seller_name = serializers.CharField(max_length=200)
    seller_type = serializers.ChoiceField(choices=SellerProfile.SellerType.choices)
    region_id = serializers.PrimaryKeyRelatedField(queryset=Region.objects.all(), source="region")
    district = serializers.CharField(max_length=100)
    description = serializers.CharField(required=False, allow_blank=True)

    def validate_phone(self, value):
        if User.objects.filter(phone=value).exists():
            raise serializers.ValidationError("A user with this phone already exists.")
        return value

    def validate_seller_name(self, value):
        if not value.strip():
            raise serializers.ValidationError("Seller name / business name is required.")
        return value.strip()

    def create(self, validated_data):
        region = validated_data.pop("region")
        profile_data = {
            "seller_name": validated_data.pop("seller_name"),
            "seller_type": validated_data.pop("seller_type"),
            "region": region,
            "district": validated_data.pop("district"),
            "description": validated_data.pop("description", ""),
            "is_verified": False,
        }
        email = validated_data.pop("email", "") or None
        user = User.objects.create_user(
            role=User.Role.SELLER,
            email=email,
            **validated_data,
        )
        SellerProfile.objects.create(user=user, **profile_data)
        return user


class BothRegisterSerializer(serializers.Serializer):
    phone = serializers.RegexField(regex=r"^\+998\d{9}$", max_length=20)
    password = serializers.CharField(write_only=True, min_length=8)
    full_name = serializers.CharField(max_length=150)
    email = serializers.EmailField(required=False, allow_blank=True)
    seller_name = serializers.CharField(max_length=200)
    seller_type = serializers.ChoiceField(choices=SellerProfile.SellerType.choices)
    region_id = serializers.PrimaryKeyRelatedField(queryset=Region.objects.all(), source="region")
    district = serializers.CharField(max_length=100)
    seller_description = serializers.CharField(required=False, allow_blank=True)
    is_business_buyer = serializers.BooleanField(default=False)
    company_name = serializers.CharField(max_length=200, required=False, allow_blank=True)

    def validate_phone(self, value):
        if User.objects.filter(phone=value).exists():
            raise serializers.ValidationError("A user with this phone already exists.")
        return value

    def create(self, validated_data):
        region = validated_data.pop("region")
        district = validated_data.pop("district")
        email = validated_data.pop("email", "") or None
        user = User.objects.create_user(
            role=User.Role.BOTH,
            email=email,
            phone=validated_data.pop("phone"),
            password=validated_data.pop("password"),
            full_name=validated_data.pop("full_name"),
        )
        BuyerProfile.objects.create(
            user=user,
            region=region,
            district=district,
            is_business_buyer=validated_data.pop("is_business_buyer", False),
            company_name=validated_data.pop("company_name", ""),
        )
        SellerProfile.objects.create(
            user=user,
            seller_name=validated_data.pop("seller_name"),
            seller_type=validated_data.pop("seller_type"),
            region=region,
            district=district,
            description=validated_data.pop("seller_description", ""),
            is_verified=False,
        )
        return user


class PublicSellerProfileSerializer(serializers.ModelSerializer):
    region = RegionBriefSerializer(read_only=True)
    user_id = serializers.UUIDField(source="user.id", read_only=True)
    full_name = serializers.CharField(source="user.full_name", read_only=True)

    class Meta:
        model = SellerProfile
        fields = (
            "user_id",
            "full_name",
            "seller_name",
            "seller_type",
            "region",
            "district",
            "description",
            "rating",
            "total_reviews",
        )
