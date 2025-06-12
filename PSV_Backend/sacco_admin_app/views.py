# sacco/admin_views.py
from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Avg, Count, Q
from django.db import transaction
from rest_framework.serializers import ValidationError
from sacco.serializers import SaccoSerializer
from sacco.models import Sacco
from routes.models import Route, RouteStop
from routes.serializers import RouteSerializer
from reviews.models import PassengerReview, OwnerReview
from reviews.serializers import PassengerReviewSerializer, OwnerReviewSerializer


class SaccoAdminPermission(permissions.BasePermission):
    """
    Custom permission to only allow sacco admins to access their own sacco's data.
    """
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_sacco_admin
    
    def has_object_permission(self, request, view, obj):
        # Check if the user is admin of the sacco being accessed
        if hasattr(obj, 'sacco'):
            return obj.sacco.sacco_admin == request.user
        elif isinstance(obj, Sacco):
            return obj.sacco_admin == request.user
        return False


class SaccoAdminDashboardView(APIView):
    """
    Dashboard overview for sacco admin showing key statistics
    """
    permission_classes = [SaccoAdminPermission]
    
    def get(self, request):
        try:
            # Get the sacco administered by this user
            sacco = Sacco.objects.get(sacco_admin=request.user)
            
            # Get basic statistics
            total_routes = Route.objects.filter(sacco=sacco).count()
            
            # Review statistics
            passenger_reviews = PassengerReview.objects.filter(sacco=sacco)
            owner_reviews = OwnerReview.objects.filter(sacco=sacco)
            
            passenger_review_count = passenger_reviews.count()
            owner_review_count = owner_reviews.count()
            
            # Average ratings
            passenger_avg_rating = passenger_reviews.aggregate(
                avg_rating=Avg('average')
            )['avg_rating'] or 0
            
            owner_avg_rating = owner_reviews.aggregate(
                avg_rating=Avg('average')
            )['avg_rating'] or 0
            
            # Recent reviews (last 5)
            recent_passenger_reviews = passenger_reviews.order_by('-created_at')[:5]
            recent_owner_reviews = owner_reviews.order_by('-created_at')[:5]
            
            dashboard_data = {
                'sacco_info': {
                    'id': sacco.id,
                    'name': sacco.name,
                    'location': sacco.location,
                    'registration_number': sacco.registration_number,
                    'contact_number': sacco.contact_number,
                    'email': sacco.email,
                    'website': sacco.website,
                    'date_established': sacco.date_established,
                },
                'statistics': {
                    'total_routes': total_routes,
                    'total_passenger_reviews': passenger_review_count,
                    'total_owner_reviews': owner_review_count,
                    'passenger_avg_rating': round(float(passenger_avg_rating), 2),
                    'owner_avg_rating': round(float(owner_avg_rating), 2),
                    'overall_avg_rating': round(
                        (float(passenger_avg_rating) + float(owner_avg_rating)) / 2, 2
                    ) if passenger_avg_rating and owner_avg_rating else 0,
                },
                'recent_reviews': {
                    'passenger_reviews': PassengerReviewSerializer(
                        recent_passenger_reviews, many=True
                    ).data,
                    'owner_reviews': OwnerReviewSerializer(
                        recent_owner_reviews, many=True
                    ).data,
                }
            }
            
            return Response(dashboard_data, status=status.HTTP_200_OK)
            
        except Sacco.DoesNotExist:
            return Response(
                {'error': 'No sacco found for this admin user'}, 
                status=status.HTTP_404_NOT_FOUND
            )


class SaccoAdminEditView(APIView):
    """
    Edit sacco details - only accessible by the admin of that sacco
    """
    permission_classes = [SaccoAdminPermission]
    
    def get(self, request):
        """Get current sacco details"""
        try:
            sacco = Sacco.objects.get(sacco_admin=request.user)
            serializer = SaccoSerializer(sacco)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Sacco.DoesNotExist:
            return Response(
                {'error': 'No sacco found for this admin user'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    def patch(self, request):
        """Update sacco details"""
        try:
            sacco = Sacco.objects.get(sacco_admin=request.user)
            serializer = SaccoSerializer(sacco, data=request.data, partial=True)
            
            if serializer.is_valid():
                serializer.save()
                return Response({
                    'message': 'Sacco details updated successfully',
                    'data': serializer.data
                }, status=status.HTTP_200_OK)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except Sacco.DoesNotExist:
            return Response(
                {'error': 'No sacco found for this admin user'}, 
                status=status.HTTP_404_NOT_FOUND
            )


class SaccoAdminRouteListView(generics.ListCreateAPIView):
    """
    List and create routes for the admin's sacco
    """
    serializer_class = RouteSerializer
    permission_classes = [SaccoAdminPermission]
    
    def get_queryset(self):
        try:
            sacco = Sacco.objects.get(sacco_admin=self.request.user)
            return Route.objects.filter(sacco=sacco).select_related('sacco').prefetch_related('stops')
        except Sacco.DoesNotExist:
            return Route.objects.none()
    
    def perform_create(self, serializer):
        try:
            sacco = Sacco.objects.get(sacco_admin=self.request.user)
            serializer.save(sacco=sacco)
        except Sacco.DoesNotExist:
            raise ValidationError("No sacco found for this admin user")


class SaccoAdminRouteDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete a specific route
    """
    serializer_class = RouteSerializer
    permission_classes = [SaccoAdminPermission]
    
    def get_queryset(self):
        try:
            sacco = Sacco.objects.get(sacco_admin=self.request.user)
            return Route.objects.filter(sacco=sacco).select_related('sacco').prefetch_related('stops')
        except Sacco.DoesNotExist:
            return Route.objects.none()


class SaccoAdminPassengerReviewsView(generics.ListAPIView):
    """
    View all passenger reviews for the admin's sacco
    """
    serializer_class = PassengerReviewSerializer
    permission_classes = [SaccoAdminPermission]
    
    def get_queryset(self):
        try:
            sacco = Sacco.objects.get(sacco_admin=self.request.user)
            return PassengerReview.objects.filter(sacco=sacco).order_by('-created_at')
        except Sacco.DoesNotExist:
            return PassengerReview.objects.none()


class SaccoAdminOwnerReviewsView(generics.ListAPIView):
    """
    View all owner reviews for the admin's sacco
    """
    serializer_class = OwnerReviewSerializer
    permission_classes = [SaccoAdminPermission]
    
    def get_queryset(self):
        try:
            sacco = Sacco.objects.get(sacco_admin=self.request.user)
            return OwnerReview.objects.filter(sacco=sacco).order_by('-created_at')
        except Sacco.DoesNotExist:
            return OwnerReview.objects.none()


class SaccoAdminAllReviewsView(APIView):
    """
    Get all reviews (both passenger and owner) for the admin's sacco
    """
    permission_classes = [SaccoAdminPermission]
    
    def get(self, request):
        try:
            sacco = Sacco.objects.get(sacco_admin=request.user)
            
            # Get passenger reviews
            passenger_reviews = PassengerReview.objects.filter(sacco=sacco).order_by('-created_at')
            # Get owner reviews
            owner_reviews = OwnerReview.objects.filter(sacco=sacco).order_by('-created_at')
            
            # Pagination parameters
            page_size = int(request.query_params.get('page_size', 10))
            passenger_page = int(request.query_params.get('passenger_page', 1))
            owner_page = int(request.query_params.get('owner_page', 1))
            
            # Paginate passenger reviews
            passenger_start = (passenger_page - 1) * page_size
            passenger_end = passenger_start + page_size
            paginated_passenger_reviews = passenger_reviews[passenger_start:passenger_end]
            
            # Paginate owner reviews
            owner_start = (owner_page - 1) * page_size
            owner_end = owner_start + page_size
            paginated_owner_reviews = owner_reviews[owner_start:owner_end]
            
            # Calculate averages
            passenger_avg = passenger_reviews.aggregate(avg=Avg('average'))['avg'] or 0
            owner_avg = owner_reviews.aggregate(avg=Avg('average'))['avg'] or 0
            
            response_data = {
                'sacco_name': sacco.name,
                'summary': {
                    'total_passenger_reviews': passenger_reviews.count(),
                    'total_owner_reviews': owner_reviews.count(),
                    'passenger_avg_rating': round(float(passenger_avg), 2),
                    'owner_avg_rating': round(float(owner_avg), 2),
                    'overall_avg_rating': round(
                        (float(passenger_avg) + float(owner_avg)) / 2, 2
                    ) if passenger_avg and owner_avg else 0,
                },
                'passenger_reviews': {
                    'data': PassengerReviewSerializer(paginated_passenger_reviews, many=True).data,
                    'page': passenger_page,
                    'page_size': page_size,
                    'total_count': passenger_reviews.count(),
                    'has_next': passenger_reviews.count() > passenger_end,
                    'has_previous': passenger_page > 1,
                },
                'owner_reviews': {
                    'data': OwnerReviewSerializer(paginated_owner_reviews, many=True).data,
                    'page': owner_page,
                    'page_size': page_size,
                    'total_count': owner_reviews.count(),
                    'has_next': owner_reviews.count() > owner_end,
                    'has_previous': owner_page > 1,
                }
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Sacco.DoesNotExist:
            return Response(
                {'error': 'No sacco found for this admin user'}, 
                status=status.HTTP_404_NOT_FOUND
            )


# Additional serializers for route management with stops
from rest_framework import serializers
from routes.models import Route, RouteStop


class RouteStopCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = RouteStop
        fields = ['stage_name', 'order']


class RouteWithStopsSerializer(serializers.ModelSerializer):
    stops = RouteStopCreateSerializer(many=True, required=False)
    sacco_name = serializers.CharField(source='sacco.name', read_only=True)
    
    class Meta:
        model = Route
        fields = [
            'id', 'start_location', 'end_location', 'distance',
            'duration', 'fare', 'sacco', 'sacco_name', 'stops'
        ]
        read_only_fields = ['sacco', 'sacco_name']
    
    @transaction.atomic
    def create(self, validated_data):
        stops_data = validated_data.pop('stops', [])
        route = Route.objects.create(**validated_data)
        
        # Create route stops
        for stop_data in stops_data:
            RouteStop.objects.create(route=route, **stop_data)
        
        return route
    
    @transaction.atomic
    def update(self, instance, validated_data):
        stops_data = validated_data.pop('stops', None)
        
        # Update route fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update stops if provided
        if stops_data is not None:
            # Delete existing stops
            instance.stops.all().delete()
            
            # Create new stops
            for stop_data in stops_data:
                RouteStop.objects.create(route=instance, **stop_data)
        
        return instance


class SaccoAdminRouteWithStopsListView(generics.ListCreateAPIView):
    """
    List and create routes with stops for the admin's sacco
    """
    serializer_class = RouteWithStopsSerializer
    permission_classes = [SaccoAdminPermission]
    
    def get_queryset(self):
        try:
            sacco = Sacco.objects.get(sacco_admin=self.request.user)
            return Route.objects.filter(sacco=sacco).select_related('sacco').prefetch_related('stops')
        except Sacco.DoesNotExist:
            return Route.objects.none()
    
    def perform_create(self, serializer):
        try:
            sacco = Sacco.objects.get(sacco_admin=self.request.user)
            serializer.save(sacco=sacco)
        except Sacco.DoesNotExist:
            raise serializers.ValidationError("No sacco found for this admin user")


class SaccoAdminRouteWithStopsDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete a specific route with stops
    """
    serializer_class = RouteWithStopsSerializer
    permission_classes = [SaccoAdminPermission]
    
    def get_queryset(self):
        try:
            sacco = Sacco.objects.get(sacco_admin=self.request.user)
            return Route.objects.filter(sacco=sacco).select_related('sacco').prefetch_related('stops')
        except Sacco.DoesNotExist:
            return Route.objects.none()
        
