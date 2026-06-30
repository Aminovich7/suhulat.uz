from django.db.models import Count
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import SellerProfile
from admin_api.filters import AdminListingFilter, AdminReviewFilter, AdminSellerFilter
from admin_api.serializers import (
    AdminListingSerializer,
    AdminReviewSerializer,
    AdminSellerSerializer,
    AdminStatsSerializer,
    ListingModerateSerializer,
    SellerRejectSerializer,
)
from common.pagination import StandardPagination
from common.permissions import IsStaffUser
from listings.models import Listing
from reviews.models import Review
from reviews.services import update_reviewee_rating


class AdminStatsView(APIView):
    permission_classes = [IsStaffUser]

    @extend_schema(responses={200: AdminStatsSerializer})
    def get(self, request):
        listings_by_status = {
            row["status"]: row["count"]
            for row in Listing.objects.values("status").annotate(count=Count("id"))
        }
        data = {
            "sellers_pending": SellerProfile.objects.filter(is_verified=False).count(),
            "sellers_total": SellerProfile.objects.count(),
            "listings_total": Listing.objects.count(),
            "listings_by_status": listings_by_status,
            "reviews_total": Review.objects.count(),
        }
        return Response(AdminStatsSerializer(data).data)


@extend_schema_view(
    list=extend_schema(description="List sellers for moderation."),
    approve=extend_schema(description="Approve seller verification."),
    reject=extend_schema(description="Reject or revoke seller verification."),
)
class AdminSellerViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    permission_classes = [IsStaffUser]
    serializer_class = AdminSellerSerializer
    pagination_class = StandardPagination
    filterset_class = AdminSellerFilter
    search_fields = ["seller_name", "user__phone", "user__full_name"]
    ordering_fields = ["user__date_joined", "seller_name"]
    ordering = ["-user__date_joined"]
    lookup_field = "user_id"

    def get_queryset(self):
        return SellerProfile.objects.select_related("user", "region")

    @action(detail=True, methods=["post"])
    def approve(self, request, user_id=None):
        profile = self.get_object()
        if profile.is_verified:
            return Response({"detail": "Seller is already verified."}, status=status.HTTP_400_BAD_REQUEST)
        profile.is_verified = True
        profile.user.is_active = True
        profile.save(update_fields=["is_verified"])
        profile.user.save(update_fields=["is_active"])
        return Response(AdminSellerSerializer(profile).data)

    @action(detail=True, methods=["post"])
    def reject(self, request, user_id=None):
        profile = self.get_object()
        serializer = SellerRejectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        profile.is_verified = False
        profile.save(update_fields=["is_verified"])

        if serializer.validated_data["deactivate_user"]:
            profile.user.is_active = False
            profile.user.save(update_fields=["is_active"])

        return Response(AdminSellerSerializer(profile).data)


@extend_schema_view(
    list=extend_schema(description="List all listings with status filters."),
    moderate=extend_schema(description="Change listing status (active/paused/deleted)."),
)
class AdminListingViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    permission_classes = [IsStaffUser]
    serializer_class = AdminListingSerializer
    pagination_class = StandardPagination
    filterset_class = AdminListingFilter
    search_fields = ["title", "description", "seller__phone"]
    ordering_fields = ["created_at", "status", "price"]
    ordering = ["-created_at"]

    def get_queryset(self):
        Listing.objects.apply_expiry()
        return Listing.objects.select_related(
            "category", "region", "seller", "seller__seller_profile"
        ).prefetch_related("images")

    @action(detail=True, methods=["post"])
    def moderate(self, request, pk=None):
        listing = self.get_object()
        serializer = ListingModerateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        listing.status = serializer.validated_data["status"]
        listing.save(update_fields=["status", "updated_at"])
        return Response(AdminListingSerializer(listing, context={"request": request}).data)


@extend_schema_view(
    list=extend_schema(description="List all reviews for moderation."),
    destroy=extend_schema(description="Remove review and recalculate seller rating."),
)
class AdminReviewViewSet(mixins.ListModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    permission_classes = [IsStaffUser]
    serializer_class = AdminReviewSerializer
    pagination_class = StandardPagination
    filterset_class = AdminReviewFilter
    search_fields = ["comment", "reviewer__phone", "reviewee__phone"]
    ordering_fields = ["created_at", "rating"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return Review.objects.select_related(
            "reviewer", "reviewee", "order", "order__listing"
        )

    def perform_destroy(self, instance):
        reviewee = instance.reviewee
        instance.delete()
        update_reviewee_rating(reviewee)
