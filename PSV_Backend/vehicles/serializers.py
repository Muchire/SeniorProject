# PSV_Backend/vehicles/serializers.py
from rest_framework import serializers
from vehicles.models import Vehicle, VehicleDocument, SaccoJoinRequest, VehicleTrip, VehiclePerformance
from sacco.serializers import SaccoSerializer
from routes.serializers import RouteSerializer
from reviews.models import OwnerReview
# from sacco.models import Sacco
from routes.models import Route
from django.db.models import Count, Avg, Sum


class VehicleDocumentSerializer(serializers.ModelSerializer):
    vehicle_registration = serializers.CharField(source='vehicle.registration_number', read_only=True)
    document_type_display = serializers.CharField(source='get_document_type_display', read_only=True)
    
    class Meta:
        model = VehicleDocument
        fields = [
            'id', 'vehicle', 'vehicle_registration', 'document_type', 
            'document_type_display', 'document_name', 'document_file',
            'expiry_date', 'is_verified', 'uploaded_at'
        ]
        read_only_fields = ['vehicle', 'is_verified', 'uploaded_at']


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


class VehicleEarningsDetailSerializer(serializers.ModelSerializer):
    """Detailed vehicle information with earnings"""
    monthly_earnings = serializers.SerializerMethodField()
    current_route = serializers.SerializerMethodField()
    owner_name = serializers.SerializerMethodField()
    performance_stats = serializers.SerializerMethodField()
    
    class Meta:
        model = Vehicle
        fields = [
            'id', 'registration_number', 'make', 'model', 'year',
            'vehicle_type', 'seating_capacity', 'fuel_type',
            'monthly_insurance', 'monthly_maintenance', 'fuel_consumption_per_km',
            'is_active', 'is_approved_by_sacco', 'date_joined_sacco',
            'owner_name', 'current_route', 'monthly_earnings', 'performance_stats'
        ]
    
    def get_owner_name(self, obj):
        return f"{obj.owner.first_name} {obj.owner.last_name}".strip() or obj.owner.username
    
    def get_current_route(self, obj):
        # Get the most frequently used route by this vehicle
        from django.db.models import Count
        most_used_route = obj.trips.values('route').annotate(
            count=Count('route')
        ).order_by('-count').first()
        
        if most_used_route:
            route = Route.objects.get(id=most_used_route['route'])
            return {
                'id': route.id,
                'name': f"{route.start_location} to {route.end_location}",
                'distance': float(route.distance),
                'fare': float(route.fare),
                'trip_count': most_used_route['count']
            }
        return None
    
    def get_monthly_earnings(self, obj):
        # Calculate earnings for all routes this vehicle operates on
        routes = Route.objects.filter(sacco=obj.sacco) if obj.sacco else Route.objects.all()
        best_route = None
        best_earnings = 0
        
        for route in routes:
            earnings = obj.calculate_monthly_earnings(route)
            if earnings['net_earnings'] > best_earnings:
                best_earnings = earnings['net_earnings']
                best_route = {
                    'route_name': f"{route.start_location} to {route.end_location}",
                    **earnings
                }
        
        return best_route
    
    def get_performance_stats(self, obj):
        # Get last 3 months performance
        from datetime import datetime, timedelta
        from django.utils import timezone
        
        three_months_ago = timezone.now().replace(day=1) - timedelta(days=90)
        performance = VehiclePerformance.objects.filter(
            vehicle=obj,
            month__gte=three_months_ago
        ).aggregate(
            total_trips=Sum('total_trips'),
            total_revenue=Sum('total_revenue'),
            total_profit=Sum('net_profit'),
            avg_occupancy=Avg('average_occupancy')
        )
        
        return {
            'total_trips_3months': performance['total_trips'] or 0,
            'total_revenue_3months': float(performance['total_revenue'] or 0),
            'total_profit_3months': float(performance['total_profit'] or 0),
            'avg_occupancy_3months': float(performance['avg_occupancy'] or 0)
        }

class SaccoJoinRequestSerializer(serializers.ModelSerializer):
    vehicle_registration = serializers.CharField(source='vehicle.registration_number', read_only=True)
    vehicle_make_model = serializers.SerializerMethodField(read_only=True)
    sacco_name = serializers.CharField(source='sacco.name', read_only=True)
    owner_name = serializers.CharField(source='owner.get_full_name', read_only=True)
    processed_by_name = serializers.CharField(source='processed_by.get_full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    preferred_routes_names = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = SaccoJoinRequest
        fields = [
            'id', 'vehicle', 'vehicle_registration', 'vehicle_make_model',
            'sacco', 'sacco_name', 'owner', 'owner_name',
            'preferred_routes', 'preferred_routes_names', 'experience_years',
            'reason_for_joining', 'status', 'status_display',
            'requested_at', 'processed_at', 'processed_by', 'processed_by_name',
            'admin_notes'
        ]
        read_only_fields = [
            'vehicle', 'sacco', 'owner', 'status', 'processed_at', 
            'processed_by', 'admin_notes'
        ]
    
    def get_vehicle_make_model(self, obj):
        return f"{obj.vehicle.make} {obj.vehicle.model}"
    
    def get_preferred_routes_names(self, obj):
        return [route.get_route_name() for route in obj.preferred_routes.all()]


class VehicleTripSerializer(serializers.ModelSerializer):
    vehicle_registration = serializers.CharField(source='vehicle.registration_number', read_only=True)
    route_name = serializers.CharField(source='route.get_route_name', read_only=True)
    duration_display = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = VehicleTrip
        fields = [
            'id', 'vehicle', 'vehicle_registration', 'route', 'route_name',
            'date', 'departure_time', 'arrival_time', 'duration_display',
            'passengers_count', 'fare_collected', 'fuel_consumed',
            'is_completed', 'notes', 'created_at'
        ]
        read_only_fields = ['duration_display', 'created_at']
    
    def get_duration_display(self, obj):
        if obj.duration:
            total_seconds = int(obj.duration.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            return f"{hours}h {minutes}m"
        return None


class VehiclePerformanceSerializer(serializers.ModelSerializer):
    vehicle_registration = serializers.CharField(source='vehicle.registration_number', read_only=True)
    vehicle_make_model = serializers.SerializerMethodField(read_only=True)
    month_display = serializers.SerializerMethodField(read_only=True)
    profit_margin = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = VehiclePerformance
        fields = [
            'id', 'vehicle', 'vehicle_registration', 'vehicle_make_model',
            'month', 'month_display', 'total_trips', 'total_distance',
            'total_passengers', 'total_revenue', 'fuel_cost',
            'maintenance_cost', 'sacco_commission', 'average_occupancy',
            'fuel_efficiency', 'net_profit', 'profit_margin',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_vehicle_make_model(self, obj):
        return f"{obj.vehicle.make} {obj.vehicle.model}"
    
    def get_month_display(self, obj):
        return obj.month.strftime('%B %Y')
    
    def get_profit_margin(self, obj):
        if obj.total_revenue > 0:
            return round((float(obj.net_profit) / float(obj.total_revenue)) * 100, 2)
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
                total_reviews=Count('id'),  # Fixed: Use Count from django.db.models, not serializers
                avg_payment_punctuality=Avg('payment_punctuality'),
                avg_support=Avg('support'),
                avg_transparency=Avg('transparency')
            ).order_by('-avg_rating')
            
            return list(sacco_stats)
        return []
class SaccoRouteDetailSerializer(serializers.ModelSerializer):
    """Route details with vehicle count and earnings"""
    vehicle_count = serializers.SerializerMethodField()
    average_earnings = serializers.SerializerMethodField()
    total_trips_today = serializers.SerializerMethodField()
    stops = serializers.SerializerMethodField()
    
    class Meta:
        model = Route
        fields = [
            'id', 'start_location', 'end_location', 'distance', 
            'duration', 'fare', 'vehicle_count', 'average_earnings',
            'total_trips_today', 'stops'
        ]
    
    def get_vehicle_count(self, obj):
        return Vehicle.objects.filter(sacco=obj.sacco, is_active=True).count()
    
    def get_average_earnings(self, obj):
        # Calculate average earnings for vehicles on this route
        vehicles = Vehicle.objects.filter(sacco=obj.sacco, is_active=True)
        if not vehicles:
            return 0
        
        total_earnings = 0
        for vehicle in vehicles:
            earnings = vehicle.calculate_monthly_earnings(obj)
            total_earnings += earnings['net_earnings']
        
        return total_earnings / vehicles.count() if vehicles else 0
    
    def get_total_trips_today(self, obj):
        from datetime import date
        from .models import VehicleTrip
        return VehicleTrip.objects.filter(
            route=obj,
            date=date.today()
        ).count()
    
    def get_stops(self, obj):
        stops = obj.stops.all().order_by('order')
        return [{'name': stop.stage_name, 'order': stop.order} for stop in stops]


class SaccoReviewSummarySerializer(serializers.ModelSerializer):
    """Summary of sacco reviews"""
    reviewer_name = serializers.SerializerMethodField()
    review_age = serializers.SerializerMethodField()
    
    class Meta:
        model = OwnerReview
        fields = [
            'id', 'reviewer_name', 'average', 'payment_punctuality',
            'driver_responsibility', 'rate_fairness', 'support',
            'transparency', 'overall', 'comment', 'review_age', 'created_at'
        ]
    
    def get_reviewer_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.username
    
    def get_review_age(self, obj):
        from datetime import datetime
        from django.utils import timezone
        
        age = timezone.now() - obj.created_at
        if age.days < 1:
            return "Today"
        elif age.days < 7:
            return f"{age.days} days ago"
        elif age.days < 30:
            return f"{age.days // 7} weeks ago"
        elif age.days < 365:
            return f"{age.days // 30} months ago"
        else:
            return f"{age.days // 365} years ago"


class EnhancedSaccoDashboardSerializer(serializers.Serializer):
    """Complete sacco dashboard with all details"""
    
    def to_representation(self, instance):
        sacco = instance
        
        # Basic sacco information
        sacco_data = {
            'id': sacco.id,
            'name': sacco.name,
            'location': sacco.location,
            'contact_number': sacco.contact_number,
            'email': sacco.email,
            'website': sacco.website,
            'date_established': sacco.date_established,
        }
        
        # Vehicle statistics
        vehicles = Vehicle.objects.filter(sacco=sacco)
        active_vehicles = vehicles.filter(is_active=True)
        
        vehicle_stats = {
            'total_vehicles': vehicles.count(),
            'active_vehicles': active_vehicles.count(),
            'pending_approval': vehicles.filter(is_approved_by_sacco=False).count(),
            'vehicle_types': list(vehicles.values('vehicle_type').annotate(
                count=Count('vehicle_type')
            )),
        }
        
        # Routes information
        routes = Route.objects.filter(sacco=sacco)
        routes_data = SaccoRouteDetailSerializer(routes, many=True).data
        
        # Vehicle details with earnings
        vehicles_data = VehicleEarningsDetailSerializer(active_vehicles, many=True).data
        
        # Financial summary
        total_estimated_monthly_revenue = 0
        total_estimated_monthly_profit = 0
        
        for vehicle in active_vehicles:
            # Get best route earnings for each vehicle
            best_earnings = 0
            best_profit = 0
            for route in routes:
                earnings = vehicle.calculate_monthly_earnings(route)
                if earnings['net_earnings'] > best_profit:
                    best_profit = earnings['net_earnings']
                    best_earnings = earnings['gross_revenue']
            
            total_estimated_monthly_revenue += best_earnings
            total_estimated_monthly_profit += best_profit
        
        financial_summary = {
            'estimated_monthly_revenue': total_estimated_monthly_revenue,
            'estimated_monthly_profit': total_estimated_monthly_profit,
            'estimated_sacco_commission': total_estimated_monthly_revenue * 0.12,
            'average_profit_per_vehicle': total_estimated_monthly_profit / active_vehicles.count() if active_vehicles else 0
        }
        reviews = OwnerReview.objects.filter(sacco=sacco).order_by('-created_at')
        ratings_summary = reviews.aggregate(
            avg_payment_punctuality=Avg('payment_punctuality'),
            avg_driver_responsibility=Avg('driver_responsibility'),
            avg_rate_fairness=Avg('rate_fairness'),
            avg_support=Avg('support'),
            avg_transparency=Avg('transparency'),
            avg_overall=Avg('overall'),
            avg_total=Avg('average'),
            total_reviews=Count('id')
        )
        
        # Convert Decimal to float for JSON serialization
        for key, value in ratings_summary.items():
            if value is not None and key != 'total_reviews':
                ratings_summary[key] = float(value)
            elif value is None and key != 'total_reviews':
                ratings_summary[key] = 0.0
        
        recent_reviews = SaccoReviewSummarySerializer(reviews[:10], many=True).data
        
        # Performance trends (last 6 months)
        from datetime import datetime, timedelta
        from django.utils import timezone
        
        six_months_ago = timezone.now().replace(day=1) - timedelta(days=180)
        monthly_performance = []
        
        current_date = six_months_ago
        while current_date <= timezone.now():
            month_performance = VehiclePerformance.objects.filter(
                vehicle__sacco=sacco,
                month__year=current_date.year,
                month__month=current_date.month
            ).aggregate(
                total_trips=Sum('total_trips'),
                total_revenue=Sum('total_revenue'),
                total_profit=Sum('net_profit'),
                avg_occupancy=Avg('average_occupancy')
            )
            
            monthly_performance.append({
                'month': current_date.strftime('%Y-%m'),
                'month_name': current_date.strftime('%B %Y'),
                'trips': month_performance['total_trips'] or 0,
                'revenue': float(month_performance['total_revenue'] or 0),
                'profit': float(month_performance['total_profit'] or 0),
                'occupancy': float(month_performance['avg_occupancy'] or 0)
            })
            
            # Move to next month
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1)
        
        return {
            'sacco_info': sacco_data,
            'vehicle_stats': vehicle_stats,
            'routes': routes_data,
            'vehicles': vehicles_data,
            'financial_summary': financial_summary,
            'ratings_summary': ratings_summary,
            'recent_reviews': recent_reviews,
            'performance_trends': monthly_performance
        }
# Enhanced Serializers (vehicles/serializers.py additions/fixes)

class ApproveRequestSerializer(serializers.Serializer):
    """Serializer for approving vehicle join requests"""
    admin_notes = serializers.CharField(
        max_length=500,
        required=False,
        allow_blank=True,
        help_text="Optional notes from admin about the approval"
    )
    
    def validate_admin_notes(self, value):
        if value:
            return value.strip()
        return value


class RejectRequestSerializer(serializers.Serializer):
    """Serializer for rejecting vehicle join requests"""
    reason = serializers.CharField(
        max_length=500,
        required=True,
        help_text="Reason for rejecting the request"
    )
    admin_notes = serializers.CharField(
        max_length=500,
        required=False,
        allow_blank=True,
        help_text="Optional additional notes from admin"
    )
    
    def validate_reason(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Rejection reason cannot be empty")
        return value.strip()
    
    def validate_admin_notes(self, value):
        if value:
            return value.strip()
        return value


class SaccoJoinRequestSerializer(serializers.ModelSerializer):
    vehicle_registration = serializers.CharField(source='vehicle.registration_number', read_only=True)
    vehicle_make_model = serializers.SerializerMethodField(read_only=True)
    sacco_name = serializers.CharField(source='sacco.name', read_only=True)
    owner_name = serializers.CharField(source='owner.get_full_name', read_only=True)
    processed_by_name = serializers.CharField(source='processed_by.get_full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    preferred_routes_names = serializers.SerializerMethodField(read_only=True)
    days_pending = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = SaccoJoinRequest
        fields = [
            'id', 'vehicle', 'vehicle_registration', 'vehicle_make_model',
            'sacco', 'sacco_name', 'owner', 'owner_name',
            'preferred_routes', 'preferred_routes_names', 'experience_years',
            'reason_for_joining', 'status', 'status_display',
            'requested_at', 'processed_at', 'processed_by', 'processed_by_name',
            # 'rejection_reason',
              'admin_notes', 'days_pending'
        ]
        read_only_fields = [
            'vehicle', 'sacco', 'owner', 'status', 'processed_at', 
            'processed_by', 
            # 'rejection_reason',
              'admin_notes'
        ]
    
    def get_vehicle_make_model(self, obj):
        return f"{obj.vehicle.make} {obj.vehicle.model}"
    
    def get_preferred_routes_names(self, obj):
        return [route.get_route_name() for route in obj.preferred_routes.all()]
    
    def get_days_pending(self, obj):
        if obj.status == 'pending':
            from django.utils import timezone
            delta = timezone.now() - obj.requested_at
            return delta.days
        return None


class SaccoAdminJoinRequestSerializer(serializers.ModelSerializer):
    """Detailed serializer for sacco admins to view join requests"""
    vehicle_details = VehicleSerializer(source='vehicle', read_only=True)
    owner_name = serializers.CharField(source='owner.get_full_name', read_only=True)
    owner_email = serializers.CharField(source='owner.email', read_only=True)
    owner_phone = serializers.CharField(source='owner.phone_number', read_only=True)
    preferred_routes_details = serializers.SerializerMethodField(read_only=True)
    vehicle_documents = serializers.SerializerMethodField(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    processed_by_name = serializers.CharField(source='processed_by.get_full_name', read_only=True)
    days_pending = serializers.SerializerMethodField(read_only=True)
    vehicle_owner_stats = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = SaccoJoinRequest
        fields = [
            'id', 'vehicle', 'vehicle_details', 'owner', 'owner_name',
            'owner_email', 'owner_phone', 'preferred_routes', 'preferred_routes_details',
            'experience_years', 'reason_for_joining', 'status', 'status_display',
            'requested_at', 'processed_at', 'processed_by', 'processed_by_name',
            # 'rejection_reason', 
            'admin_notes', 'vehicle_documents', 'days_pending',
            'vehicle_owner_stats'
        ]
        read_only_fields = ['vehicle', 'owner', 'requested_at']
    
    def get_preferred_routes_details(self, obj):
        routes = obj.preferred_routes.all()
        return [
            {
                'id': route.id,
                'name': route.get_route_name(),
                'fare': float(route.fare),
                'distance': float(route.distance),
                'duration': str(route.duration) if route.duration else None
            }
            for route in routes
        ]
    
    def get_vehicle_documents(self, obj):
        documents = VehicleDocument.objects.filter(vehicle=obj.vehicle)
        return VehicleDocumentSerializer(documents, many=True).data
    
    def get_days_pending(self, obj):
        if obj.status == 'pending':
            from django.utils import timezone
            delta = timezone.now() - obj.requested_at
            return delta.days
        return None
    
    def get_vehicle_owner_stats(self, obj):
        """Get statistics about the vehicle owner"""
        owner = obj.owner
        vehicles_count = Vehicle.objects.filter(owner=owner).count()
        active_vehicles = Vehicle.objects.filter(owner=owner, is_active=True).count()
        vehicles_in_saccos = Vehicle.objects.filter(
            owner=owner, 
            sacco__isnull=False,
            is_approved_by_sacco=True
        ).count()
        
        return {
            'total_vehicles': vehicles_count,
            'active_vehicles': active_vehicles,
            'vehicles_in_saccos': vehicles_in_saccos,
            'join_date': owner.date_joined.strftime('%Y-%m-%d') if owner.date_joined else None
        }


class JoinRequestSummarySerializer(serializers.Serializer):
    """Summary serializer for dashboard statistics"""
    total_requests = serializers.IntegerField()
    pending_requests = serializers.IntegerField()
    approved_requests = serializers.IntegerField()
    rejected_requests = serializers.IntegerField()
    requests_this_month = serializers.IntegerField()
    average_processing_days = serializers.FloatField()
    
    # Recent requests
    recent_requests = SaccoJoinRequestSerializer(many=True)
    
    # Requests by status
    requests_by_status = serializers.DictField()