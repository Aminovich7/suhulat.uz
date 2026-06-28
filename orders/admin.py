from django.contrib import admin

from orders.models import Order


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "listing",
        "buyer",
        "seller",
        "total_price",
        "status",
        "created_at",
    )
    list_filter = ("status", "fulfillment_method")
    search_fields = ("id", "buyer__phone", "seller__phone", "listing__title")
    readonly_fields = ("created_at", "updated_at")
