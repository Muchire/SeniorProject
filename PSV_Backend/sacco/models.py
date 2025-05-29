from django.db import models
from django.conf import settings
# Create your models here.
class Sacco(models.Model):
    name= models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    date_established = models.DateField(null=True, blank=True,
                                        help_text="The date the SACCO was established")
    """I'm using the date established as the registration number"""
    registration_number = models.CharField(max_length=100, unique=True)
    contact_number = models.CharField(max_length=15)
    email = models.EmailField()
    website = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    sacco_admin = models.OneToOneField(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )



    def __str__(self):
        return str(self.name  )

class SaccoAdminRequest(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    
    sacco = models.ForeignKey(Sacco, null=True, blank=True, on_delete=models.CASCADE)
    location = models.CharField(max_length=255, blank=True)
    sacco_name = models.CharField(max_length=255, blank=True)
    is_approved = models.BooleanField(default=False)
    reviewed = models.BooleanField(default=False)

    def __str__(self):
        return f" {self.user}request for {self.sacco or self.sacco_name}"
    
# class Route(models.Model):
#     start_location = models.CharField(max_length=100)
#     end_location = models.CharField(max_length=100)
#     distance = models.DecimalField(max_digits=5, decimal_places=2)
#     duration = models.DurationField()
#     fare = models.DecimalField(max_digits=10, decimal_places=2)
#     sacco = models.ForeignKey(Sacco, on_delete=models.CASCADE, related_name='routes')
    
#     def __str__(self):
#         return f"{self.start_location} to {self.end_location} with {self.sacco.name}"