from django.contrib import admin, messages

from listings.models import Category, Listing, ListingImage, Region


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ("name_uz", "name_ru", "code")
    search_fields = ("name_uz", "name_ru", "code")


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name_uz", "slug", "parent")
    search_fields = ("name_uz", "name_ru", "slug")
    prepopulated_fields = {"slug": ("name_uz",)}


class ListingImageInline(admin.TabularInline):
    model = ListingImage
    extra = 0


@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "seller",
        "listing_type",
        "price",
        "status",
        "region",
        "created_at",
    )
    list_filter = ("listing_type", "status", "region", "is_perishable")
    search_fields = ("title", "description", "seller__phone")
    inlines = [ListingImageInline]
    actions = ["mark_paused", "mark_active", "mark_deleted"]

    @admin.action(description="Pause selected listings")
    def mark_paused(self, request, queryset):
        queryset.update(status=Listing.Status.PAUSED)

    @admin.action(description="Activate selected listings")
    def mark_active(self, request, queryset):
        queryset.update(status=Listing.Status.ACTIVE)

    @admin.action(description="Soft-delete selected listings")
    def mark_deleted(self, request, queryset):
        queryset.update(status=Listing.Status.DELETED)
        self.message_user(request, "Listings marked as deleted.", messages.WARNING)
