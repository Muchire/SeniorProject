from rest_framework import serializers
from .models import Route, RouteStop
from sacco.models import Sacco

class RouteStopSerializer(serializers.ModelSerializer):
    class Meta:
        model = RouteStop
        fields = ['id', 'stage_name', 'order']

class RouteSerializer(serializers.ModelSerializer):
    stops = RouteStopSerializer(many=True, read_only=True)
    sacco_name = serializers.CharField(source='sacco.name', read_only=True)
    
    # Add financial fields
    avg_daily_trips = serializers.IntegerField(required=False, allow_null=True)
    avg_monthly_revenue = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, allow_null=True, read_only=True)
    peak_hours_multiplier = serializers.DecimalField(max_digits=3, decimal_places=2, required=False, allow_null=True)
    seasonal_variance = serializers.DecimalField(max_digits=3, decimal_places=2, required=False, allow_null=True)
    fuel_cost_per_km = serializers.DecimalField(max_digits=6, decimal_places=2, required=False, allow_null=True)
    maintenance_cost_per_month = serializers.DecimalField(max_digits=8, decimal_places=2, required=False, allow_null=True)
    
    # Calculated fields
    estimated_daily_revenue = serializers.SerializerMethodField()
    estimated_monthly_revenue = serializers.SerializerMethodField()
    
    class Meta:
        model = Route
        fields = [
            'id', 'start_location', 'end_location', 'distance', 
            'duration', 'fare', 'sacco', 'sacco_name', 'stops',
            # Financial fields
            'avg_daily_trips', 'avg_monthly_revenue', 'peak_hours_multiplier',
            'seasonal_variance', 'fuel_cost_per_km', 'maintenance_cost_per_month',
            # Calculated fields
            'estimated_daily_revenue', 'estimated_monthly_revenue'
        ]
    
    def get_estimated_daily_revenue(self, obj):
        """Calculate estimated daily revenue"""
        if obj.fare and obj.avg_daily_trips:
            return obj.fare * obj.avg_daily_trips
        return None
    
    def get_estimated_monthly_revenue(self, obj):
        """Calculate estimated monthly revenue"""
        daily_revenue = self.get_estimated_daily_revenue(obj)
        if daily_revenue:
            return daily_revenue * 30
        return None

class RouteFinancialSerializer(serializers.ModelSerializer):
    """Serializer specifically for financial data updates"""
    
    class Meta:
        model = Route
        fields = [
            'avg_daily_trips', 'peak_hours_multiplier', 'seasonal_variance',
            'fuel_cost_per_km', 'maintenance_cost_per_month', 'fare'
        ]
    
    def validate_avg_daily_trips(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Average daily trips cannot be negative")
        return value
    
    def validate_fuel_cost_per_km(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Fuel cost per km cannot be negative")
        return value
    
    def validate_maintenance_cost_per_month(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Maintenance cost cannot be negative")
        return value
    
    def validate_peak_hours_multiplier(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Peak hours multiplier cannot be negative")
        return value
    
    def validate_seasonal_variance(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Seasonal variance cannot be negative")
        return value