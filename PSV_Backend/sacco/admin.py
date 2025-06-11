from django.contrib import admin
from .models import SaccoAdminRequest, Sacco
from django.contrib import admin
from .models import SaccoAdminRequest
from django.db import transaction
import logging

logger = logging.getLogger(__name__)

class SaccoAdminRequestAdmin(admin.ModelAdmin):
    list_display = ("user", "sacco", "sacco_name", "is_approved", "reviewed")
    search_fields = ("user__username", "sacco__name", "sacco_name")
    list_filter = ("is_approved", "reviewed")
    readonly_fields = ("user",)

    @transaction.atomic
    def save_model(self, request, obj, form, change):
        """Handle approval and create new SACCO if needed."""
        logger.info(f"Admin save_model called for request {obj.id if obj.id else 'NEW'}")
        
        # Check if this is an approval (is_approved changed to True)
        if obj.is_approved and change:
            original_obj = SaccoAdminRequest.objects.get(pk=obj.pk)
            if not original_obj.is_approved:  # This is a new approval
                logger.info(f"Processing approval for user {obj.user.username}")
                
                try:
                    # Handle existing SACCO vs new SACCO
                    if obj.sacco:
                        logger.info(f"User requested admin for existing SACCO: {obj.sacco.name}")
                        sacco = obj.sacco
                    else:
                        logger.info(f"Creating new SACCO: {obj.sacco_name}")
                        
                        # Validate required fields
                        required_fields = {
                            'sacco_name': obj.sacco_name,
                            'location': obj.location,
                            'registration_number': obj.registration_number,
                            'contact_number': obj.contact_number,
                            'email': obj.email,
                        }
                        
                        missing_fields = [field for field, value in required_fields.items() if not value]
                        if missing_fields:
                            logger.error(f"Missing required fields: {missing_fields}")
                            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")

                        # Create new SACCO
                        sacco = Sacco.objects.create(
                            name=obj.sacco_name,
                            location=obj.location,
                            date_established=obj.date_established,
                            registration_number=obj.registration_number,
                            contact_number=obj.contact_number,
                            email=obj.email,
                            website=obj.website,
                        )
                        logger.info(f"Created new SACCO with ID: {sacco.id}")
                        
                        # Link the new SACCO to the request
                        obj.sacco = sacco

                    # Assign the user as admin of the SACCO
                    sacco.sacco_admin = obj.user
                    sacco.save()
                    logger.info(f"Assigned user {obj.user.username} as admin of SACCO {sacco.name}")

                    # Update user permissions
                    user = obj.user
                    logger.info(f"User before update - is_sacco_admin: {user.is_sacco_admin}, sacco_admin_requested: {user.sacco_admin_requested}")
                    
                    user.is_sacco_admin = True
                    user.sacco_admin_requested = False
                    user.save()
                    
                    # Verify the update
                    user.refresh_from_db()
                    logger.info(f"User after update - is_sacco_admin: {user.is_sacco_admin}, sacco_admin_requested: {user.sacco_admin_requested}")
                    
                    # Mark as reviewed
                    obj.reviewed = True
                    
                    logger.info(f"Successfully processed approval for user {obj.user.username}")
                    
                except Exception as e:
                    logger.error(f"Error processing approval: {str(e)}")
                    # Reset approval status if there was an error
                    obj.is_approved = False
                    raise

        # Call the parent save_model
        super().save_model(request, obj, form, change)

admin.site.register(SaccoAdminRequest, SaccoAdminRequestAdmin)

@admin.register(Sacco)
class SaccoAdmin(admin.ModelAdmin):
    list_display = ("name", "location", "registration_number", "date_established", "sacco_admin")
    search_fields = ("name", "location", "registration_number")
    ordering = ("date_established",)