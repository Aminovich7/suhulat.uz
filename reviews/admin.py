from django.contrib import admin

from reviews.models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("order", "reviewer", "reviewee", "rating", "created_at")
    list_filter = ("rating",)
    search_fields = ("comment", "reviewer__phone", "reviewee__phone")
