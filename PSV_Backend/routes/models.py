from django.db import models
from sacco.models import Sacco

# Create your models here.
class Route(models.Model):
    start_location = models.CharField(max_length=100)
    end_location = models.CharField(max_length=100)
    distance = models.DecimalField(max_digits=5, decimal_places=2)
    duration = models.DurationField()
    fare = models.DecimalField(max_digits=10, decimal_places=2)
    sacco = models.ForeignKey(Sacco, on_delete=models.CASCADE, related_name='routes')
    # Financial metrics for vehicle owners
    avg_daily_trips = models.IntegerField(null=True, blank=True)
    avg_monthly_revenue = models.DecimalField(max_digits=12, decimal_places=2,null=True, blank=True)
    peak_hours_multiplier = models.DecimalField(max_digits=3, decimal_places=2,null=True, blank=True)
    seasonal_variance = models.DecimalField(max_digits=3, decimal_places=2,null=True, blank=True)
    
    # Operating costs
    fuel_cost_per_km = models.DecimalField(max_digits=6, decimal_places=2,null=True, blank=True)
    maintenance_cost_per_month = models.DecimalField(max_digits=8, decimal_places=2,null=True, blank=True)   
    
    def __str__(self):
        return f"{self.start_location} to {self.end_location} with {self.sacco.name}"
    

class RouteStop(models.Model):
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name='stops')
    stage_name = models.CharField(max_length=100)
    order = models.PositiveIntegerField()

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.stage_name} (Route: {self.route})"