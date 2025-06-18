from django.contrib import admin
from .models import PassengerReview

@admin.register(PassengerReview)
class PassengerReviewAdmin(admin.ModelAdmin):
    list_display = ("user", "sacco", "average", "created_at")
    search_fields = ("user__username", "sacco__name", "comment")
    list_filter = ("sacco", "average", "created_at")
    ordering = ("-created_at",)
