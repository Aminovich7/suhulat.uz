from django.db.models import Q
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from common.permissions import IsBuyer, IsRFQParty
from orders.serializers import OrderSerializer
from rfq.models import RFQ
from rfq.serializers import (
    OfferCreateSerializer,
    OfferSerializer,
    RFQActionSerializer,
    RFQCreateSerializer,
    RFQSerializer,
)


@extend_schema_view(
    list=extend_schema(description="List RFQs where you are buyer or listing seller."),
    retrieve=extend_schema(description="RFQ detail with offer chain."),
    create=extend_schema(description="Create RFQ on negotiable listing (buyer)."),
)
class RFQViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        user = self.request.user
        return (
            RFQ.objects.filter(Q(buyer=user) | Q(listing__seller=user))
            .select_related("listing", "buyer")
            .prefetch_related("offers")
            .distinct()
        )

    def get_serializer_class(self):
        if self.action == "create":
            return RFQCreateSerializer
        return RFQSerializer

    def get_permissions(self):
        if self.action == "create":
            return [IsAuthenticated(), IsBuyer()]
        if self.action in ("retrieve", "counter", "accept", "reject"):
            return [IsAuthenticated(), IsRFQParty()]
        return super().get_permissions()

    @action(detail=True, methods=["post"])
    def counter(self, request, pk=None):
        rfq = self.get_object()
        serializer = OfferCreateSerializer(
            data=request.data,
            context={"request": request, "rfq": rfq},
        )
        serializer.is_valid(raise_exception=True)
        offer = serializer.save()
        return Response(OfferSerializer(offer).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def accept(self, request, pk=None):
        rfq = self.get_object()
        action_serializer = RFQActionSerializer()
        order = action_serializer.accept(rfq, request.user)
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        rfq = self.get_object()
        action_serializer = RFQActionSerializer()
        rfq = action_serializer.reject(rfq, request.user)
        return Response(RFQSerializer(rfq).data)
