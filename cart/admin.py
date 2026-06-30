from django.contrib import admin

from cart.models import Cart, CartItem


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ["user", "total_items", "created_at", "updated_at"]
    list_filter = ["created_at"]
    search_fields = ["user__phone", "user__full_name"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ["cart", "listing", "quantity", "added_at"]
    list_filter = ["added_at"]
    search_fields = ["listing__title", "cart__user__phone"]
    readonly_fields = ["id", "added_at", "updated_at"]
