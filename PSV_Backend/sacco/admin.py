from django.contrib import admin
from .models import SaccoAdminRequest, Sacco

@admin.register(SaccoAdminRequest)
class SaccoAdminRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'sacco', 'sacco_name', 'is_approved', 'reviewed')
    list_filter = ('is_approved', 'reviewed')

    def save_model(self, request, obj, form, change):
        if obj.is_approved and not obj.reviewed:
            # If no sacco exists yet, create one
            if not obj.sacco:
                sacco = Sacco.objects.create(
                    sacco_name=obj.sacco_name,
                    location=obj.location,
                    date_established=obj.date_established,
                    registration_number=obj.registration_number,
                    contact_number=obj.contact_number,
                    email=obj.email,
                    website=obj.website,
                    sacco_admin=obj.user
                )
                obj.sacco = sacco

            obj.reviewed = True  # Mark as reviewed
        super().save_model(request, obj, form, change)
from django.contrib import admin
from .models import Sacco

@admin.register(Sacco)
class SaccoAdmin(admin.ModelAdmin):
    list_display = ("name", "location", "registration_number", "date_established")
    search_fields = ("name", "location", "registration_number")
    ordering = ("date_established",)
