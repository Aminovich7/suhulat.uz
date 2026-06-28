from django.contrib import admin

from rfq.models import Offer, RFQ


class OfferInline(admin.TabularInline):
    model = Offer
    extra = 0
    readonly_fields = ("created_at",)


@admin.register(RFQ)
class RFQAdmin(admin.ModelAdmin):
    list_display = ("id", "listing", "buyer", "status", "quantity_requested", "created_at")
    list_filter = ("status",)
    search_fields = ("listing__title", "buyer__phone")
    inlines = [OfferInline]


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = ("id", "rfq", "proposed_by", "price", "quantity", "status", "created_at")
    list_filter = ("proposed_by", "status")
