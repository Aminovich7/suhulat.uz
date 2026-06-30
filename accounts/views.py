from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import SellerProfile
from accounts.serializers import (
    BuyerProfileSerializer,
    BuyerProfileUpdateSerializer,
    BuyerRegisterSerializer,
    ChangePasswordSerializer,
    LogoutSerializer,
    PublicSellerProfileSerializer,
    SellerProfileSerializer,
    SellerProfileUpdateSerializer,
    SellerRegisterSerializer,
    UserSerializer,
    UserUpdateSerializer,
)
from common.permissions import IsBuyer, IsSeller
from listings.models import Listing
from listings.serializers import ListingListSerializer
from reviews.serializers import ReviewSerializer

User = get_user_model()


class BuyerRegisterView(APIView):
    permission_classes = [AllowAny]
    serializer_class = BuyerRegisterSerializer

    @extend_schema(responses={201: UserSerializer})
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class SellerRegisterView(APIView):
    permission_classes = [AllowAny]
    serializer_class = SellerRegisterSerializer

    @extend_schema(responses={201: UserSerializer})
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == "PATCH":
            return UserUpdateSerializer
        return UserSerializer

    def get_object(self):
        return self.request.user

    @extend_schema(responses={200: UserSerializer})
    def get(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer_class()(instance)
        return Response(serializer.data)

    @extend_schema(request=UserUpdateSerializer, responses={200: UserSerializer})
    def patch(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer_class()(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserSerializer(instance).data)


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=ChangePasswordSerializer, responses={200: None})
    def post(self, request, *args, **kwargs):
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Password changed successfully."})


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=LogoutSerializer, responses={205: None})
    def post(self, request, *args, **kwargs):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_205_RESET_CONTENT)


class BuyerProfileView(APIView):
    permission_classes = [IsAuthenticated, IsBuyer]

    def get_object(self):
        profile = getattr(self.request.user, "buyer_profile", None)
        if profile is None:
            raise NotFound("Buyer profile not found.")
        return profile

    @extend_schema(responses={200: BuyerProfileSerializer})
    def get(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = BuyerProfileSerializer(instance)
        return Response(serializer.data)

    @extend_schema(request=BuyerProfileUpdateSerializer, responses={200: BuyerProfileSerializer})
    def patch(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = BuyerProfileUpdateSerializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(BuyerProfileSerializer(instance).data)


class SellerProfileView(APIView):
    permission_classes = [IsAuthenticated, IsSeller]

    def get_object(self):
        profile = getattr(self.request.user, "seller_profile", None)
        if profile is None:
            raise NotFound("Seller profile not found.")
        return profile

    @extend_schema(responses={200: SellerProfileSerializer})
    def get(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = SellerProfileSerializer(instance)
        return Response(serializer.data)

    @extend_schema(request=SellerProfileUpdateSerializer, responses={200: SellerProfileSerializer})
    def patch(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = SellerProfileUpdateSerializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(SellerProfileSerializer(instance).data)


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
