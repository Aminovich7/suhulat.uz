from django.contrib import admin, messages

from reviews.models import Review
from reviews.services import update_reviewee_rating


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("order", "reviewer", "reviewee", "rating", "created_at")
    list_filter = ("rating",)
    search_fields = ("comment", "reviewer__phone", "reviewee__phone")
    actions = ["remove_reviews"]

    @admin.action(description="Remove selected reviews (recalculates reviewee rating)")
    def remove_reviews(self, request, queryset):
        reviewees = {review.reviewee_id for review in queryset}
        count = queryset.count()
        queryset.delete()
        for user_id in reviewees:
            from django.contrib.auth import get_user_model

            user = get_user_model().objects.filter(pk=user_id).first()
            if user:
                update_reviewee_rating(user)
        self.message_user(request, f"{count} review(s) removed.", messages.WARNING)
