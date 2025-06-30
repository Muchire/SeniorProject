# PSV_Backend/vehicles/models.py
from django.db import models
from django.conf import settings
from decimal import Decimal
from sacco.models import Sacco
from routes.models import Route
from django.utils import timezone

class Vehicle(models.Model):
    VEHICLE_TYPES = [
        ('matatu', 'Matatu'),
        ('bus', 'Bus'),
        ('minibus', 'Minibus'),
        ('van', 'Van'),
    ]
    
    FUEL_TYPES = [
        ('petrol', 'Petrol'),
        ('diesel', 'Diesel'),
        ('hybrid', 'Hybrid'),
        ('electric', 'Electric'),
    ]
    
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='vehicles')
    sacco = models.ForeignKey(Sacco, on_delete=models.SET_NULL, null=True, blank=True, related_name='vehicles')
    
    # Vehicle Details
    registration_number = models.CharField(max_length=20, unique=True)
    make = models.CharField(max_length=50)
    model = models.CharField(max_length=50)
    year = models.PositiveIntegerField()
    vehicle_type = models.CharField(max_length=20, choices=VEHICLE_TYPES)
    seating_capacity = models.PositiveIntegerField()
    fuel_type = models.CharField(max_length=20, choices=FUEL_TYPES)
    
    # Financial Details
    purchase_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    current_value = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    monthly_insurance = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    monthly_maintenance = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    fuel_consumption_per_km = models.DecimalField(max_digits=5, decimal_places=2, help_text="Liters per KM")
    
    # Status
    is_active = models.BooleanField(default=True)
    is_approved_by_sacco = models.BooleanField(default=False)
    date_joined_sacco = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.make} {self.model} - {self.registration_number}"
    
    def calculate_monthly_earnings(self, route):
        """Calculate estimated monthly earnings for a specific route"""
        if not route:
            return 0
        
        # Assumptions for calculation
        trips_per_day = 8  # Average trips per day
        working_days_per_month = 26
        occupancy_rate = 0.75  # 75% average occupancy
        
        # Calculate revenue
        revenue_per_trip = route.fare * self.seating_capacity * occupancy_rate
        daily_revenue = revenue_per_trip * trips_per_day
        monthly_revenue = daily_revenue * working_days_per_month
        
        # Calculate costs
        fuel_cost_per_km = Decimal('150.0')  # Average fuel price per liter
        daily_distance = float(route.distance) * trips_per_day * 2  # Round trip
        monthly_distance = daily_distance * working_days_per_month
        monthly_fuel_cost = Decimal(monthly_distance) * self.fuel_consumption_per_km * fuel_cost_per_km
        
        # Sacco commission (typically 10-15%)
        sacco_commission = monthly_revenue * Decimal('0.12')
        
        # Total monthly costs
        total_monthly_costs = (
            monthly_fuel_cost + 
            self.monthly_insurance + 
            self.monthly_maintenance + 
            sacco_commission
        )
        
        # Net earnings
        net_earnings = monthly_revenue - total_monthly_costs
        
        return {
            'gross_revenue': float(monthly_revenue),
            'fuel_costs': float(monthly_fuel_cost),
            'insurance_costs': float(self.monthly_insurance),
            'maintenance_costs': float(self.monthly_maintenance),
            'sacco_commission': float(sacco_commission),
            'total_costs': float(total_monthly_costs),
            'net_earnings': float(net_earnings),
            'trips_per_day': trips_per_day,
            'working_days': working_days_per_month,
            'occupancy_rate': occupancy_rate,
        }


class VehicleDocument(models.Model):
    DOCUMENT_TYPES = [
        ('logbook', 'Logbook'),
        ('insurance', 'Insurance Certificate'),
        ('inspection', 'Inspection Certificate'),
        ('license', 'Driving License'),
        ('permit', 'PSV License/Permit'),
        ('ntsa', 'NTSA Certificate'),
        ('other', 'Other'),
    ]
    
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES)
    document_name = models.CharField(max_length=100)
    document_file = models.FileField(upload_to='vehicle_documents/')
    expiry_date = models.DateField(null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('vehicle', 'document_type')
    
    def __str__(self):
        return f"{self.vehicle.registration_number} - {self.get_document_type_display()}"


class SaccoJoinRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('under_review', 'Under Review'),
    ]
    
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='join_requests')
    sacco = models.ForeignKey(Sacco, on_delete=models.CASCADE, related_name='join_requests')
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    
    # Additional information
    preferred_routes = models.ManyToManyField(Route, blank=True, help_text="Routes owner is interested in")
    experience_years = models.PositiveIntegerField(help_text="Years of PSV experience")
    reason_for_joining = models.TextField()
    
    # Status and dates
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    requested_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    processed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='processed_join_requests'
    )
    admin_notes = models.TextField(blank=True, help_text="Notes from sacco admin")
    
    rejection_reason = models.TextField(blank=True, help_text="Reason for rejection")
    
    class Meta:
        unique_together = ('vehicle', 'sacco')
        ordering = ['-requested_at']
    
    def __str__(self):
        return f"{self.vehicle.registration_number} -> {self.sacco.name} ({self.status})"

class VehicleTrip(models.Model):
    """Track actual trips taken by vehicles"""
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='trips')
    route = models.ForeignKey(Route, on_delete=models.CASCADE)
    date = models.DateField()
    departure_time = models.TimeField()
    arrival_time = models.TimeField(null=True, blank=True)
    passengers_count = models.PositiveIntegerField()
    fare_collected = models.DecimalField(max_digits=8, decimal_places=2)
    fuel_consumed = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    
    # Trip status
    is_completed = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date', '-departure_time']
    
    def __str__(self):
        return f"{self.vehicle.registration_number} - {self.route} on {self.date}"
    
    @property
    def duration(self):
        if self.arrival_time and self.departure_time:
            from datetime import datetime, time
            departure = datetime.combine(self.date, self.departure_time)
            arrival = datetime.combine(self.date, self.arrival_time)
            return arrival - departure
        return None


class VehiclePerformance(models.Model):
    """Monthly performance summary for vehicles"""
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='performance_records')
    month = models.DateField()  # First day of the month
    
    # Trip statistics
    total_trips = models.PositiveIntegerField(default=0)
    total_distance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_passengers = models.PositiveIntegerField(default=0)
    total_revenue = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Costs
    fuel_cost = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    maintenance_cost = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    sacco_commission = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    
    # Performance metrics
    average_occupancy = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    fuel_efficiency = models.DecimalField(max_digits=6, decimal_places=2, default=0)  # KM per liter
    net_profit = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('vehicle', 'month')
        ordering = ['-month']
    
    def __str__(self):
        return f"{self.vehicle.registration_number} - {self.month.strftime('%B %Y')}"