from django.db.models import Q
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from common.permissions import IsBuyer, IsOrderParty
from orders.models import Order
from orders.serializers import (
    OrderCreateSerializer,
    OrderSerializer,
    OrderStatusTransitionSerializer,
)


@extend_schema_view(
    list=extend_schema(description="List orders where you are buyer or seller."),
    retrieve=extend_schema(description="Order detail for parties only."),
    create=extend_schema(description="Create order for fixed-price listing (buyer)."),
)
class OrderViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        user = self.request.user
        return Order.objects.filter(Q(buyer=user) | Q(seller=user)).distinct()

    def get_serializer_class(self):
        if self.action == "create":
            return OrderCreateSerializer
        return OrderSerializer

    def perform_create(self, serializer):
        serializer.save()

    def _transition(self, request, pk, action_name):
        order = self.get_object()
        if not IsOrderParty().has_object_permission(request, self, order):
            return Response({"detail": "Not a party to this order."}, status=status.HTTP_403_FORBIDDEN)

        serializer = OrderStatusTransitionSerializer(
            data=request.data,
            context={"request": request, "order": order, "action": action_name},
        )
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        return Response(OrderSerializer(order).data)

    @action(detail=True, methods=["post"])
    def confirm(self, request, pk=None):
        return self._transition(request, pk, "confirm")

    @action(detail=True, methods=["post"])
    def fulfilling(self, request, pk=None):
        return self._transition(request, pk, "fulfilling")

    @action(detail=True, methods=["post"])
    def delivered(self, request, pk=None):
        return self._transition(request, pk, "delivered")

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        return self._transition(request, pk, "complete")

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        return self._transition(request, pk, "cancel")

    def get_permissions(self):
        if self.action == "create":
            return [IsAuthenticated(), IsBuyer()]
        if self.action in ("retrieve", "confirm", "fulfilling", "delivered", "complete", "cancel"):
            return [IsAuthenticated(), IsOrderParty()]
        return super().get_permissions()
