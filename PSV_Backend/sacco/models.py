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
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=10.0,null=True, blank=True)  # percentage
    daily_target = models.DecimalField(max_digits=8, decimal_places=2, default=0,null=True, blank=True)
    weekly_bonus_threshold = models.DecimalField(max_digits=8, decimal_places=2, default=0,null=True, blank=True)
    weekly_bonus_amount = models.DecimalField(max_digits=8, decimal_places=2, default=0,null=True, blank=True)
    
    # Average performance metrics
    avg_vehicle_monthly_earnings = models.DecimalField(max_digits=12, decimal_places=2, default=0,null=True, blank=True)
    avg_daily_trips_per_vehicle = models.IntegerField(default=0, null=True, blank=True)

    def __str__(self):
        return str(self.name  )

class SaccoAdminRequest(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    sacco = models.ForeignKey(Sacco, null=True, blank=True, on_delete=models.CASCADE)

    sacco_name = models.CharField(max_length=255, blank=True)
    location = models.CharField(max_length=255, blank=True)
    date_established = models.DateField(null=True, blank=True)
    registration_number = models.CharField(max_length=100, blank=True)
    contact_number = models.CharField(max_length=15, blank=True)
    email = models.EmailField(blank=True)
    website = models.URLField(blank=True, null=True)

    is_approved = models.BooleanField(default=False)  # Approve status
    reviewed = models.BooleanField(default=False)  # Track review status

    def __str__(self):
        return f"{self.user.username} request for {self.sacco or self.sacco_name}"
class SaccoFinancialMetrics(models.Model):
    sacco = models.OneToOneField(Sacco, on_delete=models.CASCADE)
    
    # Revenue metrics
    total_monthly_revenue = models.DecimalField(max_digits=15, decimal_places=2, default=0, null=True, blank=True)
    avg_revenue_per_vehicle = models.DecimalField(max_digits=12, decimal_places=2, default=0, null=True, blank=True)
    revenue_growth_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0, null=True, blank=True)
    
    # Cost breakdown
    operational_costs = models.DecimalField(max_digits=12, decimal_places=2, default=0, null=True, blank=True)
    maintenance_costs = models.DecimalField(max_digits=12, decimal_places=2, default=0, null=True, blank=True)
    insurance_costs = models.DecimalField(max_digits=12, decimal_places=2, default=0, null=True, blank=True)
    licensing_costs = models.DecimalField(max_digits=12, decimal_places=2, default=0, null=True, blank=True)
    
    # Profitability
    net_profit_margin = models.DecimalField(max_digits=5, decimal_places=2, default=0, null=True, blank=True)
    owner_average_profit = models.DecimalField(max_digits=12, decimal_places=2, default=0, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)