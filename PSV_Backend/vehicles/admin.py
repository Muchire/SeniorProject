from django.contrib import admin
from django.utils import timezone
from .models import (Vehicle, VehicleDocument, SaccoJoinRequest, VehicleTrip, VehiclePerformance
)


@admin.register(SaccoJoinRequest)
class SaccoJoinRequestAdmin(admin.ModelAdmin):
    list_display = (
        'vehicle', 'sacco', 'owner', 'status', 'requested_at',
        'processed_at', 'processed_by'
    )
    list_filter = ('status', 'sacco')
    search_fields = ('vehicle__registration_number', 'owner__username', 'sacco__name')
    readonly_fields = ('requested_at',)
    actions = ['approve_requests', 'reject_requests']

    def approve_requests(self, request, queryset):
        count = 0
        for join_request in queryset:
            if join_request.status != 'approved':
                # Update the join request
                join_request.status = 'approved'
                join_request.processed_by = request.user
                join_request.processed_at = timezone.now()
                join_request.save()

                # Update the vehicle
                vehicle = join_request.vehicle
                vehicle.sacco = join_request.sacco
                vehicle.is_approved_by_sacco = True
                vehicle.date_joined_sacco = timezone.now()
                vehicle.save()

                count += 1
        self.message_user(request, f"{count} join request(s) approved and vehicles updated.")

    approve_requests.short_description = "✅ Approve selected join requests"

    def reject_requests(self, request, queryset):
        updated = queryset.update(status='rejected', processed_by=request.user, processed_at=timezone.now())
        self.message_user(request, f"{updated} join request(s) rejected.")

    reject_requests.short_description = "❌ Reject selected join requests"
