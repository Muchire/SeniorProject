from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    is_passenger = models.BooleanField(default=True)
    is_vehicle_owner = models.BooleanField(default=False)
    is_sacco_admin = models.BooleanField(default=False)  # Track admin approval
    sacco_admin_requested = models.BooleanField(default=False)  # Track request status
    phone_number = models.CharField(max_length=15, blank=True, null=True)

    def __str__(self):
        return str(self.username)
