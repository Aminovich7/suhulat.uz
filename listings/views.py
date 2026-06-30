from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from common.permissions import IsOwner, IsSeller
from listings.filters import ListingFilter
from listings.models import Category, Listing, ListingImage, Region
from listings.serializers import (
    CategorySerializer,
    ListingDetailSerializer,
    ListingImageSerializer,
    ListingImageUploadSerializer,
    ListingListSerializer,
    ListingWriteSerializer,
    RegionSerializer,
)


@extend_schema_view(
    list=extend_schema(description="Public listing catalog with filters."),
    retrieve=extend_schema(description="Public listing detail."),
    create=extend_schema(description="Create listing (seller; active requires verification)."),
    partial_update=extend_schema(description="Update own listing."),
    destroy=extend_schema(description="Soft-delete own listing."),
)
class ListingViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    filterset_class = ListingFilter
    search_fields = ["title", "description"]
    ordering_fields = ["created_at", "price"]
    ordering = ["-created_at"]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        Listing.objects.apply_expiry()
        qs = Listing.objects.select_related(
            "category", "region", "seller", "seller__seller_profile"
        ).prefetch_related("images")

        if self.action in ("list", "retrieve"):
            if self.action == "list" and self.request.query_params.get("mine", "").lower() in (
                "true",
                "1",
            ):
                if self.request.user.is_authenticated:
                    return qs.exclude(status=Listing.Status.DELETED).filter(
                        seller=self.request.user
                    )
                return qs.none()
            return qs.public()

        return qs.exclude(status=Listing.Status.DELETED).filter(seller=self.request.user)

    def get_serializer_class(self):
        if self.action in ("create", "partial_update"):
            return ListingWriteSerializer
        if self.action == "retrieve":
            return ListingDetailSerializer
        return ListingListSerializer

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [AllowAny()]
        if self.action == "create":
            return [IsAuthenticated(), IsSeller()]
        return [IsAuthenticated(), IsOwner()]

    def perform_destroy(self, instance):
        instance.status = Listing.Status.DELETED
        instance.save(update_fields=["status", "updated_at"])

    @action(
        detail=True,
        methods=["post"],
        url_path="images",
        permission_classes=[IsAuthenticated, IsOwner, IsSeller],
    )
    def upload_image(self, request, pk=None):
        listing = self.get_object()
        serializer = ListingImageUploadSerializer(
            data=request.data,
            context={"listing": listing, "request": request},
        )
        serializer.is_valid(raise_exception=True)
        image = serializer.save(listing=listing)
        return Response(
            ListingImageSerializer(image, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )

    @action(
        detail=True,
        methods=["delete"],
        url_path=r"images/(?P<image_id>\d+)",
        permission_classes=[IsAuthenticated, IsOwner],
    )
    def delete_image(self, request, pk=None, image_id=None):
        listing = self.get_object()
        image = get_object_or_404(ListingImage, pk=image_id, listing=listing)
        image.image.delete(save=False)
        image.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class RegionViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = Region.objects.all()
    serializer_class = RegionSerializer
    permission_classes = [AllowAny]
    pagination_class = None


class CategoryViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = Category.objects.filter(parent__isnull=True).prefetch_related("children")
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
    pagination_class = None

    def get_queryset(self):
        if self.action == "retrieve":
            return Category.objects.prefetch_related("children")
        return super().get_queryset()
