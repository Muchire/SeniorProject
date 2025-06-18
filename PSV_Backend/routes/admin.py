
from django.contrib import admin
from .models import Route

@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = ("start_location", "end_location", "fare", "sacco")
    search_fields = ("start_location", "end_location", "sacco__name")
    list_filter = ("sacco",)
    ordering = ("fare",)
