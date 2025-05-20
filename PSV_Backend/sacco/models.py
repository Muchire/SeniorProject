from django.db import models


# Create your models here.
class Sacco(models.Model):
    name= models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    date_established = models.DateField()
    """I'm using the date established as the registration number"""
    registration_number = models.CharField(max_length=100, unique=True)
    contact_number = models.CharField(max_length=15)
    email = models.EmailField()
    website = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)



    def __str__(self):
        return str(self.name  )

# class Route(models.Model):
#     start_location = models.CharField(max_length=100)
#     end_location = models.CharField(max_length=100)
#     distance = models.DecimalField(max_digits=5, decimal_places=2)
#     duration = models.DurationField()
#     fare = models.DecimalField(max_digits=10, decimal_places=2)
#     sacco = models.ForeignKey(Sacco, on_delete=models.CASCADE, related_name='routes')
    
#     def __str__(self):
#         return f"{self.start_location} to {self.end_location} with {self.sacco.name}"