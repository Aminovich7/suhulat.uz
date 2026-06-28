from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated

from accounts.models import SellerProfile
from reviews.models import Review
from reviews.serializers import ReviewCreateSerializer, ReviewSerializer


class ReviewCreateView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ReviewCreateSerializer

    @extend_schema(responses={201: ReviewSerializer})
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        review = serializer.save()
        from rest_framework.response import Response
        from rest_framework import status

        return Response(
            ReviewSerializer(review).data,
            status=status.HTTP_201_CREATED,
        )


class SellerReviewListView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = ReviewSerializer

    def get_queryset(self):
        seller_id = self.kwargs["seller_id"]
        get_object_or_404(SellerProfile, user_id=seller_id, is_verified=True)
        return Review.objects.filter(reviewee_id=seller_id).select_related("reviewer")
