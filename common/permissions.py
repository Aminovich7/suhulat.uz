from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsOwner(BasePermission):
    """Object owner (obj.user or obj.seller or obj.buyer depending on model)."""

    owner_field = "user"

    def has_object_permission(self, request, view, obj):
        owner = getattr(obj, self.owner_field, None)
        if owner is None and hasattr(obj, "seller"):
            owner = obj.seller
        if owner is None and hasattr(obj, "buyer"):
            owner = obj.buyer
        return owner == request.user


class IsSeller(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return user.is_authenticated and user.role in ("seller", "both")


class IsBuyer(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return user.is_authenticated and user.role in ("buyer", "both")


class IsVerifiedSeller(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if not user.is_authenticated or user.role not in ("seller", "both"):
            return False
        profile = getattr(user, "seller_profile", None)
        return profile is not None and profile.is_verified


class IsBusinessBuyer(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if not user.is_authenticated or user.role not in ("buyer", "both"):
            return False
        profile = getattr(user, "buyer_profile", None)
        return profile is not None and profile.is_business_buyer


class IsOrderParty(BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user in (obj.buyer, obj.seller)


class IsRFQParty(BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user in (obj.buyer, obj.listing.seller)
