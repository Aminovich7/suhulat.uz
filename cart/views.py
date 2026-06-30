from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from cart.models import Cart, CartItem
from cart.serializers import (
    AddToCartSerializer,
    CartItemSerializer,
    CartSerializer,
    UpdateCartItemSerializer,
)
from listings.models import Listing


def cart_listing_error(listing, user, quantity):
    if listing.listing_type != Listing.ListingType.FIXED:
        return "Only fixed-price listings can be added to the cart."
    if listing.seller_id == user.id:
        return "Cannot add your own listing to the cart."
    if listing.status != Listing.Status.ACTIVE:
        return "This listing is no longer available."
    if listing.price is None:
        return "Listing has no price."
    if quantity <= 0:
        return "Quantity must be positive."
    if quantity > listing.quantity_available:
        return f"Available quantity: {listing.quantity_available}"
    if listing.minimum_order_quantity and quantity < listing.minimum_order_quantity:
        return f"Minimum order quantity is {listing.minimum_order_quantity}."
    return None


@extend_schema_view(
    list=extend_schema(description="Get the authenticated user's cart."),
)
class CartViewSet(viewsets.GenericViewSet):
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "delete", "head", "options"]

    def get_cart(self):
        cart, _ = Cart.objects.get_or_create(user=self.request.user)
        return cart

    def list(self, request, *args, **kwargs):
        cart = self.get_cart()
        serializer = self.get_serializer(cart)
        return Response(serializer.data)

    @extend_schema(request=AddToCartSerializer, responses={201: CartItemSerializer})
    @action(detail=False, methods=["post"], serializer_class=AddToCartSerializer)
    def add_item(self, request):
        serializer = AddToCartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        cart = self.get_cart()
        listing = get_object_or_404(Listing, id=serializer.validated_data["listing_id"])
        quantity = serializer.validated_data["quantity"]

        cart_item = CartItem.objects.filter(cart=cart, listing=listing).first()
        new_quantity = quantity if cart_item is None else cart_item.quantity + quantity

        error = cart_listing_error(listing, request.user, new_quantity)
        if error:
            return Response({"detail": error}, status=status.HTTP_400_BAD_REQUEST)

        if cart_item is None:
            cart_item = CartItem.objects.create(cart=cart, listing=listing, quantity=quantity)
            created = True
        else:
            cart_item.quantity = new_quantity
            cart_item.save()
            created = False

        return Response(
            CartItemSerializer(cart_item).data,
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

        cart = self.get_cart()
        cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
        cart_item.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(request=UpdateCartItemSerializer, responses={200: CartItemSerializer})
    @action(detail=False, methods=["post"], serializer_class=UpdateCartItemSerializer)
    def update_item(self, request):
        item_id = request.data.get("item_id")
        if not item_id:
            return Response(
                {"detail": "item_id is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = UpdateCartItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        cart = self.get_cart()
        cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
        quantity = serializer.validated_data["quantity"]

        error = cart_listing_error(cart_item.listing, request.user, quantity)
        if error:
            return Response({"detail": error}, status=status.HTTP_400_BAD_REQUEST)

        cart_item.quantity = quantity
        cart_item.save()

        return Response(CartItemSerializer(cart_item).data)

    @action(detail=False, methods=["delete"])
    def clear(self, request):
        cart = self.get_cart()
        cart.items.all().delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
