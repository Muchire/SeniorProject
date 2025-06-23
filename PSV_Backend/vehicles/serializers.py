# PSV_Backend/vehicles/serializers.py
from rest_framework import serializers
from vehicles.models import Vehicle, VehicleDocument, SaccoJoinRequest, VehicleTrip, VehiclePerformance
from sacco.serializers import SaccoSerializer
from routes.serializers import RouteSerializer
from reviews.models import OwnerReview


class VehicleDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = VehicleDocument
        fields = [
            'id', 'document_type', 'document_name', 'document_file',
            'expiry_date', 'is_verified', 'uploaded_at'
        ]
        read_only_fields = ['is_verified', 'uploaded_at']


class VehicleSerializer(serializers.ModelSerializer):
    owner_name = serializers.CharField(source='owner.username', read_only=True)
    sacco_name = serializers.CharField(source='sacco.name', read_only=True)
    documents = VehicleDocumentSerializer(many=True, read_only=True)
    
    class Meta:
        model = Vehicle
        fields = [
            'id', 'registration_number', 'make', 'model', 'year',
            'vehicle_type', 'seating_capacity', 'fuel_type',
            'purchase_price', 'current_value', 'monthly_insurance',
            'monthly_maintenance', 'fuel_consumption_per_km',
            'is_active', 'is_approved_by_sacco', 'date_joined_sacco',
            'owner', 'owner_name', 'sacco', 'sacco_name',
            'documents', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'owner', 'owner_name', 'sacco_name', 'is_approved_by_sacco',
            'date_joined_sacco', 'created_at', 'updated_at'
        ]

    def create(self, validated_data):
        # Remove sacco from validated_data if present, as new vehicles shouldn't have a sacco initially
        validated_data.pop('sacco', None)
        return super().create(validated_data)


class VehicleEarningsSerializer(serializers.Serializer):
    """Serializer for vehicle earnings calculations"""
    route_id = serializers.IntegerField()
    route_name = serializers.CharField(read_only=True)
    gross_revenue = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    fuel_costs = serializers.DecimalField(max_digits=8, decimal_places=2, read_only=True)
    insurance_costs = serializers.DecimalField(max_digits=8, decimal_places=2, read_only=True)
    maintenance_costs = serializers.DecimalField(max_digits=8, decimal_places=2, read_only=True)
    sacco_commission = serializers.DecimalField(max_digits=8, decimal_places=2, read_only=True)
    total_costs = serializers.DecimalField(max_digits=8, decimal_places=2, read_only=True)
    net_earnings = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    trips_per_day = serializers.IntegerField(read_only=True)
    working_days = serializers.IntegerField(read_only=True)
    occupancy_rate = serializers.DecimalField(max_digits=4, decimal_places=2, read_only=True)


class SaccoJoinRequestSerializer(serializers.ModelSerializer):
    sacco_name = serializers.CharField(source='sacco.name', read_only=True)
    vehicle_registration = serializers.CharField(source='vehicle.registration_number', read_only=True)
    owner_name = serializers.CharField(source='owner.username', read_only=True)
    preferred_routes = RouteSerializer(many=True, read_only=True)
    preferred_route_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = SaccoJoinRequest
        fields = [
            'id', 'vehicle', 'vehicle_registration', 'sacco', 'sacco_name',
            'owner', 'owner_name', 'preferred_routes', 'preferred_route_ids',
            'experience_years', 'reason_for_joining', 'status',
            'requested_at', 'processed_at', 'processed_by', 'admin_notes'
        ]
        read_only_fields = [
            'owner', 'owner_name', 'vehicle_registration', 'sacco_name',
            'status', 'requested_at', 'processed_at', 'processed_by', 'admin_notes'
        ]
    
    def create(self, validated_data):
        preferred_route_ids = validated_data.pop('preferred_route_ids', [])
        join_request = super().create(validated_data)
        
        if preferred_route_ids:
            from routes.models import Route
            routes = Route.objects.filter(id__in=preferred_route_ids)
            join_request.preferred_routes.set(routes)
        
        return join_request


class VehicleTripSerializer(serializers.ModelSerializer):
    route_name = serializers.CharField(source='route.__str__', read_only=True)
    vehicle_registration = serializers.CharField(source='vehicle.registration_number', read_only=True)
    duration = serializers.CharField(read_only=True)
    
    class Meta:
        model = VehicleTrip
        fields = [
            'id', 'vehicle', 'vehicle_registration', 'route', 'route_name',
            'date', 'departure_time', 'arrival_time', 'duration',
            'passengers_count', 'fare_collected', 'fuel_consumed',
            'is_completed', 'notes', 'created_at'
        ]
        read_only_fields = ['vehicle_registration', 'route_name', 'duration', 'created_at']


class VehiclePerformanceSerializer(serializers.ModelSerializer):
    vehicle_registration = serializers.CharField(source='vehicle.registration_number', read_only=True)
    month_name = serializers.CharField(source='month', read_only=True)
    profit_margin = serializers.SerializerMethodField()
    
    class Meta:
        model = VehiclePerformance
        fields = [
            'id', 'vehicle', 'vehicle_registration', 'month', 'month_name',
            'total_trips', 'total_distance', 'total_passengers', 'total_revenue',
            'fuel_cost', 'maintenance_cost', 'sacco_commission',
            'average_occupancy', 'fuel_efficiency', 'net_profit', 'profit_margin',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['vehicle_registration', 'month_name', 'profit_margin', 'created_at', 'updated_at']
    
    def get_profit_margin(self, obj):
        if obj.total_revenue > 0:
            return round((obj.net_profit / obj.total_revenue) * 100, 2)
        return 0


class VehicleOwnerDashboardSerializer(serializers.Serializer):
    """Serializer for vehicle owner dashboard summary"""
    total_vehicles = serializers.IntegerField()
    active_vehicles = serializers.IntegerField()
    vehicles_in_sacco = serializers.IntegerField()
    pending_requests = serializers.IntegerField()
    
    # Current month stats
    current_month_trips = serializers.IntegerField()
    current_month_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    current_month_profit = serializers.DecimalField(max_digits=12, decimal_places=2)
    
    # Recent activity
    recent_trips = VehicleTripSerializer(many=True)
    recent_reviews = serializers.SerializerMethodField()
    
    def get_recent_reviews(self, obj):
        # Get recent owner reviews for the user's vehicles' saccos
        user = self.context.get('user')
        if user:
            recent_reviews = OwnerReview.objects.filter(
                user=user
            ).order_by('-created_at')[:5]
            
            return [{
                'id': review.id,
                'sacco_name': review.sacco.name,
                'average': float(review.average),
                'overall': review.overall,
                'created_at': review.created_at.strftime('%Y-%m-%d'),
                'comment': review.comment[:100] + '...' if len(review.comment) > 100 else review.comment
            } for review in recent_reviews]
        return []


class VehicleOwnerReviewsSerializer(serializers.Serializer):
    """Serializer for reviews by vehicle owners"""
    sacco_reviews = serializers.SerializerMethodField()
    sacco_comparison = serializers.SerializerMethodField()
    
    def get_sacco_reviews(self, obj):
        """Get all reviews by this vehicle owner"""
        user = self.context.get('user')
        if user:
            from reviews.serializers import OwnerReviewSerializer
            reviews = OwnerReview.objects.filter(user=user).order_by('-created_at')
            return OwnerReviewSerializer(reviews, many=True).data
        return []
    
    def get_sacco_comparison(self, obj):
        """Compare saccos based on vehicle owner reviews"""
        user = self.context.get('user')
        if user:
            # Get average ratings for each sacco from all vehicle owners
            from django.db.models import Avg
            sacco_stats = OwnerReview.objects.values(
                'sacco__name', 'sacco__id'
            ).annotate(
                avg_rating=Avg('average'),
                total_reviews=serializers.Count('id'),
                avg_payment_punctuality=Avg('payment_punctuality'),
                avg_support=Avg('support'),
                avg_transparency=Avg('transparency')
            ).order_by('-avg_rating')
            
            return list(sacco_stats)
        return []
