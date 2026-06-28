from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import SellerProfile
from accounts.serializers import (
    BuyerProfileSerializer,
    BuyerRegisterSerializer,
    BothRegisterSerializer,
    PublicSellerProfileSerializer,
    SellerProfileSerializer,
    SellerRegisterSerializer,
    UserSerializer,
    UserUpdateSerializer,
)
from listings.models import Listing
from listings.serializers import ListingListSerializer
from reviews.serializers import ReviewSerializer

User = get_user_model()


class BuyerRegisterView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = BuyerRegisterSerializer

    @extend_schema(responses={201: UserSerializer})
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class SellerRegisterView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = SellerRegisterSerializer

    @extend_schema(responses={201: UserSerializer})
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class BothRegisterView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = BothRegisterSerializer

    @extend_schema(responses={201: UserSerializer})
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class MeView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return UserUpdateSerializer
        return UserSerializer

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserSerializer(instance).data)


class BuyerProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = BuyerProfileSerializer

    def get_object(self):
        profile = getattr(self.request.user, "buyer_profile", None)
        if profile is None:
            from rest_framework.exceptions import NotFound

            raise NotFound("Buyer profile not found.")
        return profile


class SellerProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = SellerProfileSerializer

    def get_object(self):
        profile = getattr(self.request.user, "seller_profile", None)
        if profile is None:
            from rest_framework.exceptions import NotFound

            raise NotFound("Seller profile not found.")
        return profile


class PublicSellerProfileView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, user_id):
        profile = get_object_or_404(
            SellerProfile.objects.select_related("region", "user"),
            user_id=user_id,
            is_verified=True,
        )
        Listing.objects.apply_expiry()
        listings = (
            Listing.objects.public()
            .filter(seller_id=user_id)
            .select_related("category", "region")[:20]
        )
        reviews = profile.user.reviews_received.select_related("reviewer").order_by(
            "-created_at"
        )[:20]

        return Response(
            {
                "profile": PublicSellerProfileSerializer(profile).data,
                "listings": ListingListSerializer(listings, many=True).data,
                "reviews": ReviewSerializer(reviews, many=True).data,
            }
        )
