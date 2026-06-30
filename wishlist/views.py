from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from listings.models import Listing
from wishlist.models import Wishlist, WishlistItem
from wishlist.serializers import (
    AddToWishlistSerializer,
    WishlistItemSerializer,
    WishlistSerializer,
)


@extend_schema_view(
    list=extend_schema(description="Get the authenticated user's wishlist."),
)
class WishlistViewSet(viewsets.GenericViewSet):
    serializer_class = WishlistSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "delete", "head", "options"]

    def get_wishlist(self):
        wishlist, _ = Wishlist.objects.get_or_create(user=self.request.user)
        return wishlist

    def list(self, request, *args, **kwargs):
        wishlist = self.get_wishlist()
        serializer = self.get_serializer(wishlist)
        return Response(serializer.data)

    @extend_schema(request=AddToWishlistSerializer, responses={201: WishlistItemSerializer})
    @action(detail=False, methods=["post"], serializer_class=AddToWishlistSerializer)
    def add_item(self, request):
        serializer = AddToWishlistSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        wishlist = self.get_wishlist()
        listing = get_object_or_404(Listing, id=serializer.validated_data["listing_id"])

        wishlist_item, created = WishlistItem.objects.get_or_create(
            wishlist=wishlist,
            listing=listing,
        )

        return Response(
            WishlistItemSerializer(wishlist_item).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    @action(detail=False, methods=["post"])
    def remove_item(self, request):
        item_id = request.data.get("item_id")
        if not item_id:
            return Response(
                {"detail": "item_id is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        wishlist = self.get_wishlist()
        wishlist_item = get_object_or_404(WishlistItem, id=item_id, wishlist=wishlist)
        wishlist_item.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["delete"])
    def clear(self, request):
        wishlist = self.get_wishlist()
        wishlist.items.all().delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
