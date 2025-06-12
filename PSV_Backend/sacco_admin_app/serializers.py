# sacco/admin_serializers.py
from rest_framework import serializers
from sacco.models import Sacco
from routes.models import Route, RouteStop
from reviews.models import PassengerReview, OwnerReview


class SaccoAdminSerializer(serializers.ModelSerializer):
    """Enhanced serializer for sacco admin panel"""
    total_routes = serializers.SerializerMethodField()
    total_passenger_reviews = serializers.SerializerMethodField()
    total_owner_reviews = serializers.SerializerMethodField()
    avg_passenger_rating = serializers.SerializerMethodField()
    avg_owner_rating = serializers.SerializerMethodField()
    
    class Meta:
        model = Sacco
        fields = [
            'id', 'name', 'location', 'date_established', 
            'registration_number', 'contact_number', 'email', 
            'website', 'created_at', 'total_routes',
            'total_passenger_reviews', 'total_owner_reviews',
            'avg_passenger_rating', 'avg_owner_rating'
        ]
        read_only_fields = ['created_at', 'total_routes', 'total_passenger_reviews',
                          'total_owner_reviews', 'avg_passenger_rating', 'avg_owner_rating']
    
    def get_total_routes(self, obj):
        return obj.routes.count()
    
    def get_total_passenger_reviews(self, obj):
        return obj.passenger_reviews.count()
    
    def get_total_owner_reviews(self, obj):
        return obj.owner_reviews.count()
    
    def get_avg_passenger_rating(self, obj):
        reviews = obj.passenger_reviews.all()
        if reviews.exists():
            return round(sum(review.average for review in reviews) / reviews.count(), 2)
        return 0.0
    
    def get_avg_owner_rating(self, obj):
        reviews = obj.owner_reviews.all()
        if reviews.exists():
            return round(sum(review.average for review in reviews) / reviews.count(), 2)
        return 0.0


class RouteStopAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = RouteStop
        fields = ['id', 'stage_name', 'order']


class RouteAdminSerializer(serializers.ModelSerializer):
    """Enhanced route serializer for admin panel"""
    stops = RouteStopAdminSerializer(many=True, read_only=True)
    stops_data = RouteStopAdminSerializer(many=True, write_only=True, required=False)
    sacco_name = serializers.CharField(source='sacco.name', read_only=True)
    total_stops = serializers.SerializerMethodField()
    
    class Meta:
        model = Route
        fields = [
            'id', 'start_location', 'end_location', 'distance',
            'duration', 'fare', 'sacco', 'sacco_name', 'stops',
            'stops_data', 'total_stops'
        ]
        read_only_fields = ['sacco', 'sacco_name', 'total_stops']
    
    def get_total_stops(self, obj):
        return obj.stops.count()
    
    def create(self, validated_data):
        stops_data = validated_data.pop('stops_data', [])
        route = Route.objects.create(**validated_data)
        
        # Create route stops
        for stop_data in stops_data:
            RouteStop.objects.create(route=route, **stop_data)
        
        return route
    
    def update(self, instance, validated_data):
        stops_data = validated_data.pop('stops_data', None)
        
        # Update route fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update stops if provided
        if stops_data is not None:
            # Delete existing stops and create new ones
            instance.stops.all().delete()
            for stop_data in stops_data:
                RouteStop.objects.create(route=instance, **stop_data)
        
        return instance


class PassengerReviewAdminSerializer(serializers.ModelSerializer):
    """Enhanced passenger review serializer for admin panel"""
    user_name = serializers.CharField(source='user.username', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    sacco_name = serializers.CharField(source='sacco.name', read_only=True)
    created_at_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = PassengerReview
        fields = [
            'id', 'user', 'user_name', 'user_email', 'sacco', 'sacco_name',
            'cleanliness', 'punctuality', 'comfort', 'overall', 'average',
            'comment', 'created_at', 'created_at_formatted'
        ]
        read_only_fields = ['user', 'sacco', 'average', 'created_at']
    
    def get_created_at_formatted(self, obj):
        return obj.created_at.strftime('%Y-%m-%d %H:%M:%S')


class OwnerReviewAdminSerializer(serializers.ModelSerializer):
    """Enhanced owner review serializer for admin panel"""
    user_name = serializers.CharField(source='user.username', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    sacco_name = serializers.CharField(source='sacco.name', read_only=True)
    created_at_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = OwnerReview
        fields = [
            'id', 'user', 'user_name', 'user_email', 'sacco', 'sacco_name',
            'payment_punctuality', 'driver_responsibility', 'rate_fairness',
            'support', 'transparency', 'overall', 'average', 'comment',
            'created_at', 'created_at_formatted'
        ]
        read_only_fields = ['user', 'sacco', 'average', 'created_at']
    
    def get_created_at_formatted(self, obj):
        return obj.created_at.strftime('%Y-%m-%d %H:%M:%S')


class ReviewSummarySerializer(serializers.Serializer):
    """Serializer for review summary statistics"""
    total_reviews = serializers.IntegerField()
    average_rating = serializers.FloatField()
    rating_distribution = serializers.DictField()
    recent_reviews = serializers.ListField()
    
    def to_representation(self, instance):
        # This is a custom serializer for summary data
        return instance


class DashboardStatsSerializer(serializers.Serializer):
    """Serializer for dashboard statistics"""
    sacco_info = SaccoAdminSerializer()
    route_stats = serializers.DictField()
    review_stats = serializers.DictField()
    recent_activity = serializers.ListField()
    
    def to_representation(self, instance):
        return instance