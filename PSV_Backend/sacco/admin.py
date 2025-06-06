from django.contrib import admin
from .models import SaccoAdminRequest, Sacco

from django.contrib import admin
from .models import SaccoAdminRequest

class SaccoAdminRequestAdmin(admin.ModelAdmin):
    list_display = ("user", "sacco", "is_approved", "reviewed")
    search_fields = ("user__username", "sacco__name")

    def save_model(self, request, obj, form, change):
        """Ensure approval updates the user."""
        super().save_model(request, obj, form, change)

        if obj.is_approved and obj.sacco:
            obj.sacco.sacco_admin = obj.user
            obj.sacco.save()

            user = obj.user
            user.is_sacco_admin = True
            user.sacco_admin_requested = False
            user.save()

admin.site.register(SaccoAdminRequest, SaccoAdminRequestAdmin)

@admin.register(Sacco)
class SaccoAdmin(admin.ModelAdmin):
    list_display = ("name", "location", "registration_number", "date_established")
    search_fields = ("name", "location", "registration_number")
    ordering = ("date_established",)
