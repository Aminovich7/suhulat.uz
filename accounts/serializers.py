from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
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

    class Meta:
        model = BuyerProfile
        fields = (
            "region",
            "district",
            "is_business_buyer",
            "company_name",
            "rating",
            "total_reviews",
        )


class BuyerProfileUpdateSerializer(serializers.ModelSerializer):
    region_id = serializers.PrimaryKeyRelatedField(
        queryset=Region.objects.all(),
        source="region",
        required=False,
    )

    class Meta:
        model = BuyerProfile
        fields = (
            "region_id",
            "district",
            "is_business_buyer",
            "company_name",
        )

    def validate(self, attrs):
        is_business = attrs.get(
            "is_business_buyer",
            getattr(self.instance, "is_business_buyer", False),
        )
        company_name = attrs.get(
            "company_name",
            getattr(self.instance, "company_name", ""),
        )
        if is_business and not company_name.strip():
            raise serializers.ValidationError(
                {"company_name": "Company name is required for business buyers."}
            )
        return attrs


class SellerProfileSerializer(serializers.ModelSerializer):
    region = RegionBriefSerializer(read_only=True)

    class Meta:
        model = SellerProfile
        fields = (
            "seller_name",
            "seller_type",
            "region",
            "district",
            "description",
            "is_verified",
            "rating",
            "total_reviews",
        )


class SellerProfileUpdateSerializer(serializers.ModelSerializer):
    region_id = serializers.PrimaryKeyRelatedField(
        queryset=Region.objects.all(),
        source="region",
        required=False,
    )

    class Meta:
        model = SellerProfile
        fields = (
            "seller_name",
            "seller_type",
            "region_id",
            "district",
            "description",
        )

    def validate_seller_name(self, value):
        if not value.strip():
            raise serializers.ValidationError("Seller name / business name is required.")
        return value.strip()


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
            "is_staff",
            "date_joined",
            "buyer_profile",
            "seller_profile",
        )
        read_only_fields = fields


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("email", "full_name")


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
    new_password_confirm = serializers.CharField(write_only=True, min_length=8)

    def validate_old_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value

    def validate(self, attrs):
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError(
                {"new_password_confirm": "New passwords do not match."}
            )
        validate_password(attrs["new_password"], self.context["request"].user)
        return attrs

    def save(self, **kwargs):
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save(update_fields=["password"])
        return user


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()

    def validate(self, attrs):
        from rest_framework_simplejwt.tokens import RefreshToken

        try:
            token = RefreshToken(attrs["refresh"])
        except Exception as exc:
            raise serializers.ValidationError({"refresh": "Invalid or expired token."}) from exc
        attrs["token"] = token
        return attrs

    def save(self, **kwargs):
        self.validated_data["token"].blacklist()
        return {}


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

    def validate(self, attrs):
        if attrs.get("is_business_buyer") and not attrs.get("company_name", "").strip():
            raise serializers.ValidationError(
                {"company_name": "Company name is required for business buyers."}
            )
        return attrs

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
