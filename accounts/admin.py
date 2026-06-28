from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib import admin, messages
from django.contrib.auth import get_user_model

from accounts.models import BuyerProfile, SellerProfile

User = get_user_model()


class BuyerProfileInline(admin.StackedInline):
    model = BuyerProfile
    extra = 0


class SellerProfileInline(admin.StackedInline):
    model = SellerProfile
    extra = 0
    readonly_fields = ("rating", "total_reviews")


@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):
    ordering = ("phone",)
    list_display = ("phone", "full_name", "role", "is_active", "is_staff", "date_joined")
    list_filter = ("role", "is_active", "is_staff")
    search_fields = ("phone", "full_name", "email")
    inlines = [BuyerProfileInline, SellerProfileInline]

    fieldsets = (
        (None, {"fields": ("phone", "password")}),
        ("Personal", {"fields": ("full_name", "email", "role")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("phone", "full_name", "role", "password1", "password2"),
            },
        ),
    )


@admin.register(SellerProfile)
class SellerProfileAdmin(admin.ModelAdmin):
    list_display = ("seller_name", "user", "seller_type", "region", "is_verified", "rating")
    list_filter = ("seller_type", "is_verified", "region")
    search_fields = ("seller_name", "user__phone", "user__full_name")
    actions = ["approve_sellers", "revoke_verification"]

    @admin.action(description="Approve selected sellers")
    def approve_sellers(self, request, queryset):
        updated = queryset.update(is_verified=True)
        self.message_user(request, f"{updated} seller(s) approved.", messages.SUCCESS)

    @admin.action(description="Revoke verification")
    def revoke_verification(self, request, queryset):
        updated = queryset.update(is_verified=False)
        self.message_user(request, f"{updated} seller(s) unverified.", messages.WARNING)


@admin.register(BuyerProfile)
class BuyerProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "region", "district", "is_business_buyer")
    list_filter = ("is_business_buyer", "region")
