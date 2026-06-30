from django.contrib import admin

from wishlist.models import Wishlist, WishlistItem


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ["user", "total_items", "created_at", "updated_at"]
    list_filter = ["created_at"]
    search_fields = ["user__phone", "user__full_name"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(WishlistItem)
class WishlistItemAdmin(admin.ModelAdmin):
    list_display = ["wishlist", "listing", "added_at"]
    list_filter = ["added_at"]
    search_fields = ["listing__title", "wishlist__user__phone"]
    readonly_fields = ["id", "added_at"]
