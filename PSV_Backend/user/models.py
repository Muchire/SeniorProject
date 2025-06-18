from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    # These represent capabilities/permissions (what roles user can access)
    is_passenger = models.BooleanField(default=True)
    is_vehicle_owner = models.BooleanField(default=False)
    is_sacco_admin = models.BooleanField(default=False)  # Track admin approval
    sacco_admin_requested = models.BooleanField(default=False)  # Track request status
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    
    # Add this field to track the currently active role
    ROLE_CHOICES = [
        ('passenger', 'Passenger'),
        ('vehicle_owner', 'Vehicle Owner'),
        ('sacco_admin', 'Sacco Admin'),
    ]
    current_role = models.CharField(
        max_length=20, 
        choices=ROLE_CHOICES, 
        default='passenger'
    )

    def __str__(self):
        return str(self.username)