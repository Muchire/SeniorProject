from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import api_view, permission_classes
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count, Avg, Sum
from django.utils import timezone
from django.db import transaction
from .serializers import (
    EnhancedSaccoDashboardSerializer, VehicleSerializer, VehicleDocumentSerializer, SaccoJoinRequestSerializer,
    VehicleTripSerializer, VehiclePerformanceSerializer,
    VehicleOwnerDashboardSerializer, VehicleOwnerReviewsSerializer,RejectRequestSerializer,ApproveRequestSerializer, SaccoAdminJoinRequestSerializer
)
from reviews.serializers import OwnerReviewSerializer
from routes.models import Route
from sacco.models import Sacco
from reviews.models import OwnerReview
from .models import Vehicle, VehicleDocument, SaccoJoinRequest, VehicleTrip, VehiclePerformance
from vehicles.email_service import SaccoEmailService
import logging

logger = logging.getLogger(__name__)


class VehicleOwnerPermission(permissions.BasePermission):
    """Custom permission to ensure only vehicle owners can access vehicle owner features"""
    
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and 
            request.user.is_vehicle_owner and 
            request.user.current_role == 'vehicle_owner'
        )


class VehicleListCreateView(generics.ListCreateAPIView):
    serializer_class = VehicleSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Vehicle.objects.filter(owner=self.request.user).order_by('-created_at')
    
    def perform_create(self, serializer):
        # Save the vehicle with the current user as owner
        vehicle = serializer.save(owner=self.request.user)
        
        # Update user to be a vehicle owner if they aren't already
        user = self.request.user
        if not user.is_vehicle_owner:
            user.is_vehicle_owner = True
            user.save(update_fields=['is_vehicle_owner'])
        
        return vehicle

class VehicleDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = VehicleSerializer
    permission_classes = [VehicleOwnerPermission]
    
    def get_queryset(self):
        return Vehicle.objects.filter(owner=self.request.user)


class VehicleDocumentView(generics.ListCreateAPIView):
    serializer_class = VehicleDocumentSerializer
    permission_classes = [VehicleOwnerPermission]
    
    def get_queryset(self):
        vehicle_id = self.kwargs.get('vehicle_id')
        vehicle = get_object_or_404(Vehicle, id=vehicle_id, owner=self.request.user)
        return VehicleDocument.objects.filter(vehicle=vehicle)
    
    def perform_create(self, serializer):
        vehicle_id = self.kwargs.get('vehicle_id')
        vehicle = get_object_or_404(Vehicle, id=vehicle_id, owner=self.request.user)
        serializer.save(vehicle=vehicle)


class VehicleDocumentDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = VehicleDocumentSerializer
    permission_classes = [VehicleOwnerPermission]
    
    def get_queryset(self):
        vehicle_id = self.kwargs.get('vehicle_id')
        return VehicleDocument.objects.filter(
            vehicle_id=vehicle_id,
            vehicle__owner=self.request.user
        )


class VehicleEarningsEstimationView(APIView):
    """Calculate estimated earnings for a vehicle on different routes"""
    permission_classes = [VehicleOwnerPermission]
    
    def get(self, request, vehicle_id):
        vehicle = get_object_or_404(Vehicle, id=vehicle_id, owner=request.user)
        
        # Get all routes or filter by sacco if vehicle is in one
        routes = Route.objects.all()
        sacco_id = request.query_params.get('sacco_id')
        
        if sacco_id:
            routes = routes.filter(sacco_id=sacco_id)
        elif vehicle.sacco:
            routes = routes.filter(sacco=vehicle.sacco)
        
        earnings_data = []
        for route in routes:
            calculation = vehicle.calculate_monthly_earnings(route)
            earnings_data.append({
                'route_id': route.id,
                'route_name': str(route),
                'route_distance': float(route.distance),
                'route_fare': float(route.fare),
                'sacco_name': route.sacco.name,
                'sacco_id': route.sacco.id,
                **calculation
            })
        
        # Sort by net earnings (highest first)
        earnings_data.sort(key=lambda x: x['net_earnings'], reverse=True)
        
        return Response({
            'vehicle': VehicleSerializer(vehicle).data,
            'earnings_estimations': earnings_data
        })


class VehicleTripView(generics.ListCreateAPIView):
    serializer_class = VehicleTripSerializer
    permission_classes = [VehicleOwnerPermission]
    
    def get_queryset(self):
        vehicle_id = self.kwargs.get('vehicle_id')
        vehicle = get_object_or_404(Vehicle, id=vehicle_id, owner=self.request.user)
        return VehicleTrip.objects.filter(vehicle=vehicle).order_by('-date', '-departure_time')
    
    def perform_create(self, serializer):
        vehicle_id = self.kwargs.get('vehicle_id')
        vehicle = get_object_or_404(Vehicle, id=vehicle_id, owner=self.request.user)
        serializer.save(vehicle=vehicle)


class VehiclePerformanceView(generics.ListAPIView):
    serializer_class = VehiclePerformanceSerializer
    permission_classes = [VehicleOwnerPermission]
    
    def get_queryset(self):
        vehicle_id = self.kwargs.get('vehicle_id')
        vehicle = get_object_or_404(Vehicle, id=vehicle_id, owner=self.request.user)
        return VehiclePerformance.objects.filter(vehicle=vehicle).order_by('-month')


class VehicleOwnerDashboardView(APIView):
    """Main dashboard view for vehicle owners"""
    permission_classes = [VehicleOwnerPermission]
    
    def get(self, request):
        user = request.user
        current_month = timezone.now().replace(day=1).date()
        
        # Get vehicle statistics
        vehicles = Vehicle.objects.filter(owner=user)
        total_vehicles = vehicles.count()
        active_vehicles = vehicles.filter(is_active=True).count()
        vehicles_in_sacco = vehicles.filter(sacco__isnull=False).count()
        
        # Get pending join requests
        pending_requests = SaccoJoinRequest.objects.filter(
            owner=user,
            status='pending'
        ).count()
        
        # Get current month performance
        current_month_performance = VehiclePerformance.objects.filter(
            vehicle__owner=user,
            month=current_month
        ).aggregate(
            total_trips=Sum('total_trips'),
            total_revenue=Sum('total_revenue'),
            total_profit=Sum('net_profit')
        )
        
        # Get recent trips (last 10)
        recent_trips = VehicleTrip.objects.filter(
            vehicle__owner=user
        ).order_by('-date', '-departure_time')[:10]
        
        dashboard_data = {
            'total_vehicles': total_vehicles,
            'active_vehicles': active_vehicles,
            'vehicles_in_sacco': vehicles_in_sacco,
            'pending_requests': pending_requests,
            'current_month_trips': current_month_performance['total_trips'] or 0,
            'current_month_revenue': current_month_performance['total_revenue'] or 0,
            'current_month_profit': current_month_performance['total_profit'] or 0,
            'recent_trips': VehicleTripSerializer(recent_trips, many=True).data,
            'recent_reviews': []  # Will be populated by serializer
        }
        
        serializer = VehicleOwnerDashboardSerializer(dashboard_data, context={'user': user})
        return Response(serializer.data)


class VehicleOwnerReviewsView(APIView):
    """Get reviews and sacco comparisons for vehicle owners"""
    permission_classes = [VehicleOwnerPermission]
    
    def get(self, request):
        serializer = VehicleOwnerReviewsSerializer(
            {}, 
            context={'user': request.user}
        )
        return Response(serializer.data)


class AvailableSaccosView(APIView):
    """Get all available saccos with their ratings and routes"""
    permission_classes = [VehicleOwnerPermission]
    
    def get(self, request):
        from sacco.serializers import SaccoSerializer
        from routes.serializers import RouteSerializer
        
        saccos = Sacco.objects.all().annotate(
            avg_owner_rating=Avg('owner_reviews__average'),
            total_owner_reviews=Count('owner_reviews'),
            avg_passenger_rating=Avg('passenger_reviews__average'),
            total_passenger_reviews=Count('passenger_reviews'),
            total_routes=Count('routes')
        )
        
        sacco_data = []
        for sacco in saccos:
            routes = Route.objects.filter(sacco=sacco)
            sacco_info = {
                'id': sacco.id,
                'name': sacco.name,
                'location': sacco.location,
                'contact_number': sacco.contact_number,
                'email': sacco.email,
                'website': sacco.website,
                'avg_owner_rating': float(sacco.avg_owner_rating or 0),
                'total_owner_reviews': sacco.total_owner_reviews,
                'avg_passenger_rating': float(sacco.avg_passenger_rating or 0),
                'total_passenger_reviews': sacco.total_passenger_reviews,
                'total_routes': sacco.total_routes,
                'routes': RouteSerializer(routes, many=True).data
            }
            sacco_data.append(sacco_info)
        
        # Sort by owner rating
        sacco_data.sort(key=lambda x: x['avg_owner_rating'], reverse=True)
        
        return Response({
            'saccos': sacco_data,
            'total_count': len(sacco_data)
        })


class SaccoDetailsView(APIView):
    """Get detailed information about a specific sacco"""
    permission_classes = [VehicleOwnerPermission]
    
    def get(self, request, sacco_id):
        sacco = get_object_or_404(Sacco, id=sacco_id)
        
        # Get routes
        routes = Route.objects.filter(sacco=sacco)
        
        # Get owner reviews
        owner_reviews = OwnerReview.objects.filter(sacco=sacco).order_by('-created_at')
        
        # Calculate average ratings
        avg_ratings = owner_reviews.aggregate(
            avg_payment_punctuality=Avg('payment_punctuality'),
            avg_driver_responsibility=Avg('driver_responsibility'),
            avg_rate_fairness=Avg('rate_fairness'),
            avg_support=Avg('support'),
            avg_transparency=Avg('transparency'),
            avg_overall=Avg('overall'),
            avg_total=Avg('average')
        )
        
        # Get recent reviews
        recent_reviews = []
        for review in owner_reviews[:10]:
            recent_reviews.append({
                'id': review.id,
                'reviewer': review.user.username,
                'average': float(review.average),
                'payment_punctuality': review.payment_punctuality,
                'driver_responsibility': review.driver_responsibility,
                'rate_fairness': review.rate_fairness,
                'support': review.support,
                'transparency': review.transparency,
                'overall': review.overall,
                'comment': review.comment,
                'created_at': review.created_at.strftime('%Y-%m-%d')
            })
        
        from routes.serializers import RouteSerializer
        
        return Response({
            'sacco': {
                'id': sacco.id,
                'name': sacco.name,
                'location': sacco.location,
                'contact_number': sacco.contact_number,
                'email': sacco.email,
                'website': sacco.website,
                'date_established': sacco.date_established,
                'total_vehicles': Vehicle.objects.filter(sacco=sacco).count(),
                'active_vehicles': Vehicle.objects.filter(sacco=sacco, is_active=True).count()
            },
            'routes': RouteSerializer(routes, many=True).data,
            'ratings': {
                'average_rating': float(avg_ratings['avg_total'] or 0),
                'total_reviews': owner_reviews.count(),
                'payment_punctuality': float(avg_ratings['avg_payment_punctuality'] or 0),
                'driver_responsibility': float(avg_ratings['avg_driver_responsibility'] or 0),
                'rate_fairness': float(avg_ratings['avg_rate_fairness'] or 0),
                'support': float(avg_ratings['avg_support'] or 0),
                'transparency': float(avg_ratings['avg_transparency'] or 0),
                'overall': float(avg_ratings['avg_overall'] or 0)
            },
            'recent_reviews': recent_reviews
        })


class RouteListView(APIView):
    """Get all routes with sacco information"""
    permission_classes = [VehicleOwnerPermission]
    
    def get(self, request):
        from routes.serializers import RouteSerializer
        
        routes = Route.objects.select_related('sacco').all()
        sacco_id = request.query_params.get('sacco_id')
        
        if sacco_id:
            routes = routes.filter(sacco_id=sacco_id)
        
        route_data = []
        for route in routes:
            route_info = {
                'id': route.id,
                'start_location': route.start_location,
                'end_location': route.end_location,
                'distance': float(route.distance),
                'duration': str(route.duration),
                'fare': float(route.fare),
                'sacco': {
                    'id': route.sacco.id,
                    'name': route.sacco.name,
                    'location': route.sacco.location
                },
                'stops': []
            }
            
            # Get route stops
            stops = route.stops.all().order_by('order')
            for stop in stops:
                route_info['stops'].append({
                    'id': stop.id,
                    'stage_name': stop.stage_name,
                    'order': stop.order
                })
            
            route_data.append(route_info)
        
        return Response({
            'routes': route_data,
            'total_count': len(route_data)
        })


class CreateOwnerReviewView(generics.CreateAPIView):
    """Create or update a review for a sacco as a vehicle owner"""
    permission_classes = [VehicleOwnerPermission]
    serializer_class = OwnerReviewSerializer

    def create(self, request, *args, **kwargs):
        sacco_id = kwargs.get('sacco_id')
        sacco = get_object_or_404(Sacco, id=sacco_id)

        # Check if user has already reviewed this sacco
        existing_review = OwnerReview.objects.filter(
            user=request.user,
            sacco=sacco
        ).first()

        if existing_review:
            serializer = self.get_serializer(existing_review, data=request.data, partial=True)
        else:
            serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            serializer.save(user=request.user, sacco=sacco)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VehicleStatsView(APIView):
    """Get statistics for a specific vehicle"""
    permission_classes = [VehicleOwnerPermission]
    
    def get(self, request, vehicle_id):
        vehicle = get_object_or_404(Vehicle, id=vehicle_id, owner=request.user)
        
        # Get current month stats
        current_month = timezone.now().replace(day=1).date()
        current_month_performance = VehiclePerformance.objects.filter(
            vehicle=vehicle,
            month=current_month
        ).first()
        
        # Get all-time stats
        all_time_stats = VehiclePerformance.objects.filter(
            vehicle=vehicle
        ).aggregate(
            total_trips=Sum('total_trips'),
            total_distance=Sum('total_distance'),
            total_revenue=Sum('total_revenue'),
            total_profit=Sum('net_profit'),
            avg_occupancy=Avg('average_occupancy'),
            avg_fuel_efficiency=Avg('fuel_efficiency')
        )
        
        # Get recent trips
        recent_trips = VehicleTrip.objects.filter(
            vehicle=vehicle
        ).order_by('-date', '-departure_time')[:20]
        
        return Response({
            'vehicle': VehicleSerializer(vehicle).data,
            'current_month': {
                'trips': current_month_performance.total_trips if current_month_performance else 0,
                'distance': float(current_month_performance.total_distance) if current_month_performance else 0,
                'revenue': float(current_month_performance.total_revenue) if current_month_performance else 0,
                'profit': float(current_month_performance.net_profit) if current_month_performance else 0,
                'occupancy': float(current_month_performance.average_occupancy) if current_month_performance else 0,
                'fuel_efficiency': float(current_month_performance.fuel_efficiency) if current_month_performance else 0
            },
            'all_time': {
                'total_trips': all_time_stats['total_trips'] or 0,
                'total_distance': float(all_time_stats['total_distance'] or 0),
                'total_revenue': float(all_time_stats['total_revenue'] or 0),
                'total_profit': float(all_time_stats['total_profit'] or 0),
                'avg_occupancy': float(all_time_stats['avg_occupancy'] or 0),
                'avg_fuel_efficiency': float(all_time_stats['avg_fuel_efficiency'] or 0)
            },
            'recent_trips': VehicleTripSerializer(recent_trips, many=True).data
        })


class SaccoSearchView(APIView):
    """Search saccos with filters"""
    permission_classes = [VehicleOwnerPermission]
    
    def get(self, request):
        from sacco.serializers import SaccoSerializer
        
        # Get query parameters
        search = request.query_params.get('search', '')
        route = request.query_params.get('route', '')
        location = request.query_params.get('location', '')
        min_rating = request.query_params.get('min_rating', None)
        
        # Start with all saccos
        saccos = Sacco.objects.all().annotate(
            avg_owner_rating=Avg('owner_reviews__average'),
            total_owner_reviews=Count('owner_reviews'),
            avg_passenger_rating=Avg('passenger_reviews__average'),
            total_passenger_reviews=Count('passenger_reviews'),
            total_routes=Count('routes')
        )
        
        # Apply filters
        if search:
            saccos = saccos.filter(
                Q(name__icontains=search) | 
                Q(location__icontains=search)
            )
        
        if location:
            saccos = saccos.filter(location__icontains=location)
            
        if route:
            saccos = saccos.filter(
                routes__start_location__icontains=route
            ).distinct()
            
        if min_rating:
            try:
                min_rating = float(min_rating)
                saccos = saccos.filter(avg_owner_rating__gte=min_rating)
            except ValueError:
                pass
        
        # Serialize data
        sacco_data = []
        for sacco in saccos:
            routes = Route.objects.filter(sacco=sacco)
            sacco_info = {
                'id': sacco.id,
                'name': sacco.name,
                'location': sacco.location,
                'contact_number': sacco.contact_number,
                'email': sacco.email,
                'website': sacco.website,
                'avg_owner_rating': float(sacco.avg_owner_rating or 0),
                'total_owner_reviews': sacco.total_owner_reviews,
                'avg_passenger_rating': float(sacco.avg_passenger_rating or 0),
                'total_passenger_reviews': sacco.total_passenger_reviews,
                'total_routes': sacco.total_routes,
            }
            sacco_data.append(sacco_info)
        
        # Sort by rating
        sacco_data.sort(key=lambda x: x['avg_owner_rating'], reverse=True)
        
        return Response({
            'saccos': sacco_data,
            'total_count': len(sacco_data),
            'filters_applied': {
                'search': search,
                'route': route,
                'location': location,
                'min_rating': min_rating
            }
        })


class SaccoDashboardView(APIView):
    """Get dashboard data for a specific sacco"""
    permission_classes = [VehicleOwnerPermission]
    
    def get(self, request, sacco_id):
        sacco = get_object_or_404(Sacco, id=sacco_id)
        
        # Get basic stats
        total_vehicles = Vehicle.objects.filter(sacco=sacco).count()
        active_vehicles = Vehicle.objects.filter(sacco=sacco, is_active=True).count()
        total_routes = Route.objects.filter(sacco=sacco).count()
        
        # Get review stats
        owner_reviews = OwnerReview.objects.filter(sacco=sacco)
        avg_rating = owner_reviews.aggregate(avg=Avg('average'))['avg'] or 0
        
        # Get recent performance (you might need to adjust this based on your models)
        current_month = timezone.now().replace(day=1).date()
        monthly_stats = VehiclePerformance.objects.filter(
            vehicle__sacco=sacco,
            month=current_month
        ).aggregate(
            total_trips=Sum('total_trips'),
            total_revenue=Sum('total_revenue'),
            total_distance=Sum('total_distance')
        )
        
        return Response({
            'sacco': {
                'id': sacco.id,
                'name': sacco.name,
                'location': sacco.location,
                'contact_number': sacco.contact_number,
                'email': sacco.email
            },
            'stats': {
                'total_vehicles': total_vehicles,
                'active_vehicles': active_vehicles,
                'total_routes': total_routes,
                'average_rating': float(avg_rating),
                'total_reviews': owner_reviews.count(),
                'current_month_trips': monthly_stats['total_trips'] or 0,
                'current_month_revenue': float(monthly_stats['total_revenue'] or 0),
                'current_month_distance': float(monthly_stats['total_distance'] or 0)
            }
        })


class CompareSaccosView(APIView):
    """Compare multiple saccos"""
    permission_classes = [VehicleOwnerPermission]
    
    def post(self, request):
        sacco_ids = request.data.get('sacco_ids', [])
        
        if not sacco_ids or len(sacco_ids) < 2:
            return Response(
                {'error': 'Please provide at least 2 sacco IDs for comparison'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        comparison_data = []
        
        for sacco_id in sacco_ids:
            try:
                sacco = Sacco.objects.get(id=sacco_id)
                
                # Get stats
                total_vehicles = Vehicle.objects.filter(sacco=sacco).count()
                routes = Route.objects.filter(sacco=sacco)
                
                # Get reviews
                owner_reviews = OwnerReview.objects.filter(sacco=sacco)
                avg_ratings = owner_reviews.aggregate(
                    avg_payment_punctuality=Avg('payment_punctuality'),
                    avg_driver_responsibility=Avg('driver_responsibility'),
                    avg_rate_fairness=Avg('rate_fairness'),
                    avg_support=Avg('support'),
                    avg_transparency=Avg('transparency'),
                    avg_overall=Avg('overall'),
                    avg_total=Avg('average')
                )
                
                sacco_data = {
                    'id': sacco.id,
                    'name': sacco.name,
                    'location': sacco.location,
                    'total_vehicles': total_vehicles,
                    'total_routes': routes.count(),
                    'established': sacco.date_established.strftime('%Y-%m-%d') if sacco.date_established else None,
                    'ratings': {
                        'average': float(avg_ratings['avg_total'] or 0),
                        'payment_punctuality': float(avg_ratings['avg_payment_punctuality'] or 0),
                        'driver_responsibility': float(avg_ratings['avg_driver_responsibility'] or 0),
                        'rate_fairness': float(avg_ratings['avg_rate_fairness'] or 0),
                        'support': float(avg_ratings['avg_support'] or 0),
                        'transparency': float(avg_ratings['avg_transparency'] or 0),
                        'overall': float(avg_ratings['avg_overall'] or 0),
                        'total_reviews': owner_reviews.count()
                    },
                    'routes': [{
                        'id': route.id,
                        'name': str(route),
                        'distance': float(route.distance),
                        'fare': float(route.fare)
                    } for route in routes][:5]  # Limit to 5 routes for comparison
                }
                
                comparison_data.append(sacco_data)
                
            except Sacco.DoesNotExist:
                return Response(
                    {'error': f'Sacco with ID {sacco_id} not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        return Response({
            'comparison': comparison_data,
            'compared_at': timezone.now().isoformat()
        })


class VehicleDocumentUploadView(APIView):
    permission_classes = [VehicleOwnerPermission]
    
    def post(self, request, vehicle_id):
        try:
            vehicle = get_object_or_404(Vehicle, id=vehicle_id, owner=request.user)
            
            document_type = request.data.get('document_type')
            document_file = request.FILES.get('document_file')  # Changed from 'document'
            document_name = request.data.get('document_name', '')
            
            if not document_type or not document_file:
                return Response(
                    {'error': 'Both document_type and document_file are required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check if document type is valid
            valid_types = [choice[0] for choice in VehicleDocument.DOCUMENT_TYPES]
            if document_type not in valid_types:
                return Response(
                    {'error': f'Invalid document type. Must be one of: {", ".join(valid_types)}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check if document already exists for this vehicle and type
            existing_doc = VehicleDocument.objects.filter(
                vehicle=vehicle,
                document_type=document_type
            ).first()
            
            if existing_doc:
                # Update existing document
                existing_doc.document_file = document_file
                existing_doc.document_name = document_name
                existing_doc.expiry_date = request.data.get('expiry_date')
                existing_doc.save()
                
                serializer = VehicleDocumentSerializer(existing_doc)
                return Response({
                    'message': 'Document updated successfully',
                    'document': serializer.data
                }, status=status.HTTP_200_OK)
            else:
                # Create new document
                document_data = {
                    'document_type': document_type,
                    'document_file': document_file,
                    'document_name': document_name,
                    'expiry_date': request.data.get('expiry_date')
                }
                
                serializer = VehicleDocumentSerializer(data=document_data)
                if serializer.is_valid():
                    serializer.save(vehicle=vehicle)
                    return Response({
                        'message': 'Document uploaded successfully',
                        'document': serializer.data
                    }, status=status.HTTP_201_CREATED)
                
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
class VehicleMaintenanceView(APIView):
    """
    Track vehicle maintenance records
    """
    permission_classes = [VehicleOwnerPermission]
    
    def get(self, request, vehicle_id):
        vehicle = get_object_or_404(Vehicle, id=vehicle_id, owner=request.user)
        
        # This assumes you have a VehicleMaintenance model
        # If not, you can create maintenance tracking through VehicleTrip or similar
        maintenance_records = []
        
        return Response({
            'vehicle_id': vehicle.id,
            'maintenance_records': maintenance_records,
            'next_service_due': None,  # Calculate based on mileage/time
            'maintenance_alerts': []
        })
    
    def post(self, request, vehicle_id):
        vehicle = get_object_or_404(Vehicle, id=vehicle_id, owner=request.user)
        
        # Add maintenance record logic here
        maintenance_data = request.data
        
        return Response({
            'message': 'Maintenance record added successfully',
            'data': maintenance_data
        }, status=status.HTTP_201_CREATED)


class VehicleRevenueAnalyticsView(APIView):
    """
    Detailed revenue analytics for a vehicle
    """
    permission_classes = [VehicleOwnerPermission]
    
    def get(self, request, vehicle_id):
        vehicle = get_object_or_404(Vehicle, id=vehicle_id, owner=request.user)
        
        # Get date range from query params
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        # Default to current month if no dates provided
        if not start_date or not end_date:
            current_date = timezone.now().date()
            start_date = current_date.replace(day=1)
            end_date = current_date
        else:
            from datetime import datetime
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        # Get trips in date range
        trips = VehicleTrip.objects.filter(
            vehicle=vehicle,
            date__gte=start_date,
            date__lte=end_date
        )
        
        # Calculate analytics
        total_trips = trips.count()
        total_revenue = sum(trip.revenue for trip in trips if trip.revenue)
        total_distance = sum(trip.distance_covered for trip in trips if trip.distance_covered)
        
        # Group by date for trend analysis
        daily_revenue = {}
        for trip in trips:
            date_str = trip.date.strftime('%Y-%m-%d')
            if date_str not in daily_revenue:
                daily_revenue[date_str] = {'trips': 0, 'revenue': 0, 'distance': 0}
            
            daily_revenue[date_str]['trips'] += 1
            daily_revenue[date_str]['revenue'] += float(trip.revenue or 0)
            daily_revenue[date_str]['distance'] += float(trip.distance_covered or 0)
        
        # Convert to list format for frontend
        daily_data = [
            {
                'date': date,
                'trips': data['trips'],
                'revenue': data['revenue'],
                'distance': data['distance']
            }
            for date, data in sorted(daily_revenue.items())
        ]
        
        return Response({
            'vehicle': VehicleSerializer(vehicle).data,
            'period': {
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d')
            },
            'summary': {
                'total_trips': total_trips,
                'total_revenue': float(total_revenue or 0),
                'total_distance': float(total_distance or 0),
                'average_revenue_per_trip': float(total_revenue / total_trips) if total_trips > 0 else 0,
                'average_distance_per_trip': float(total_distance / total_trips) if total_trips > 0 else 0
            },
            'daily_breakdown': daily_data
        })


class VehicleComparisonView(APIView):
    """
    Compare performance between user's vehicles
    """
    permission_classes = [VehicleOwnerPermission]
    
    def get(self, request):
        vehicles = Vehicle.objects.filter(owner=request.user)
        
        if vehicles.count() < 2:
            return Response({
                'message': 'You need at least 2 vehicles to compare performance',
                'vehicles': VehicleSerializer(vehicles, many=True).data
            })
        
        comparison_data = []
        current_month = timezone.now().replace(day=1).date()
        
        for vehicle in vehicles:
            # Get current month performance
            performance = VehiclePerformance.objects.filter(
                vehicle=vehicle,
                month=current_month
            ).first()
            
            # Get all-time stats
            all_time_stats = VehiclePerformance.objects.filter(
                vehicle=vehicle
            ).aggregate(
                total_trips=Sum('total_trips'),
                total_revenue=Sum('total_revenue'),
                avg_efficiency=Avg('fuel_efficiency')
            )
            
            vehicle_data = {
                'vehicle': VehicleSerializer(vehicle).data,
                'current_month': {
                    'trips': performance.total_trips if performance else 0,
                    'revenue': float(performance.total_revenue) if performance else 0,
                    'profit': float(performance.net_profit) if performance else 0,
                    'efficiency': float(performance.fuel_efficiency) if performance else 0
                },
                'all_time': {
                    'total_trips': all_time_stats['total_trips'] or 0,
                    'total_revenue': float(all_time_stats['total_revenue'] or 0),
                    'avg_efficiency': float(all_time_stats['avg_efficiency'] or 0)
                }
            }
            comparison_data.append(vehicle_data)
        
        # Sort by current month revenue
        comparison_data.sort(
            key=lambda x: x['current_month']['revenue'], 
            reverse=True
        )
        
        return Response({
            'comparison': comparison_data,
            'best_performer': comparison_data[0] if comparison_data else None,
            'total_vehicles': len(comparison_data)
        })


class VehicleAlertView(APIView):
    """
    Get alerts and notifications for vehicles
    """
    permission_classes = [VehicleOwnerPermission]
    
    def get(self, request):
        vehicles = Vehicle.objects.filter(owner=request.user)
        alerts = []
        
        for vehicle in vehicles:
            # Check document expiry
            documents = VehicleDocument.objects.filter(vehicle=vehicle)
            for doc in documents:
                if doc.expiry_date:
                    days_to_expiry = (doc.expiry_date - timezone.now().date()).days
                    if days_to_expiry <= 30:  # Alert 30 days before expiry
                        alerts.append({
                            'type': 'document_expiry',
                            'vehicle_id': vehicle.id,
                            'vehicle_name': f"{vehicle.make} {vehicle.model}",
                            'message': f"{doc.get_document_type_display()} expires in {days_to_expiry} days",
                            'severity': 'high' if days_to_expiry <= 7 else 'medium',
                            'date': doc.expiry_date.strftime('%Y-%m-%d')
                        })
            
            # Check if vehicle is inactive
            if not vehicle.is_active:
                alerts.append({
                    'type': 'inactive_vehicle',
                    'vehicle_id': vehicle.id,
                    'vehicle_name': f"{vehicle.make} {vehicle.model}",
                    'message': 'Vehicle is marked as inactive',
                    'severity': 'low'
                })
            
            # Check for pending join requests
            pending_requests = SaccoJoinRequest.objects.filter(
                vehicle=vehicle,
                status='pending'
            ).count()
            
            if pending_requests > 0:
                alerts.append({
                    'type': 'pending_request',
                    'vehicle_id': vehicle.id,
                    'vehicle_name': f"{vehicle.make} {vehicle.model}",
                    'message': f'{pending_requests} pending SACCO join request(s)',
                    'severity': 'medium'
                })
        
        # Sort alerts by severity
        severity_order = {'high': 0, 'medium': 1, 'low': 2}
        alerts.sort(key=lambda x: severity_order.get(x.get('severity', 'low'), 2))
        
        return Response({
            'alerts': alerts,
            'total_alerts': len(alerts),
            'high_priority': len([a for a in alerts if a.get('severity') == 'high']),
            'medium_priority': len([a for a in alerts if a.get('severity') == 'medium']),
            'low_priority': len([a for a in alerts if a.get('severity') == 'low'])
        })


class VehicleExportDataView(APIView):
    """
    Export vehicle data for reporting
    """
    permission_classes = [VehicleOwnerPermission]
    
    def get(self, request):
        from django.http import HttpResponse
        import csv
        
        vehicle_id = request.query_params.get('vehicle_id')
        export_type = request.query_params.get('type', 'trips')  # trips, performance, documents
        
        if vehicle_id:
            vehicles = Vehicle.objects.filter(id=vehicle_id, owner=request.user)
        else:
            vehicles = Vehicle.objects.filter(owner=request.user)
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="vehicle_{export_type}.csv"'
        
        writer = csv.writer(response)
        
        if export_type == 'trips':
            writer.writerow(['Vehicle', 'Date', 'Route', 'Departure', 'Arrival', 'Distance', 'Revenue', 'Expenses'])
            
            for vehicle in vehicles:
                trips = VehicleTrip.objects.filter(vehicle=vehicle).order_by('-date')
                for trip in trips:
                    writer.writerow([
                        f"{vehicle.make} {vehicle.model}",
                        trip.date.strftime('%Y-%m-%d'),
                        trip.route.name if trip.route else 'N/A',
                        trip.departure_time.strftime('%H:%M') if trip.departure_time else 'N/A',
                        trip.arrival_time.strftime('%H:%M') if trip.arrival_time else 'N/A',
                        trip.distance_covered or 0,
                        trip.revenue or 0,
                        trip.expenses or 0
                    ])
        
        elif export_type == 'performance':
            writer.writerow(['Vehicle', 'Month', 'Total Trips', 'Distance', 'Revenue', 'Profit', 'Efficiency'])
            
            for vehicle in vehicles:
                performances = VehiclePerformance.objects.filter(vehicle=vehicle).order_by('-month')
                for perf in performances:
                    writer.writerow([
                        f"{vehicle.make} {vehicle.model}",
                        perf.month.strftime('%Y-%m'),
                        perf.total_trips,
                        perf.total_distance,
                        perf.total_revenue,
                        perf.net_profit,
                        perf.fuel_efficiency
                    ])
        
        return response
class SaccoJoinRequestView(generics.ListCreateAPIView):
    """
    List all join requests for the authenticated user or create a new one
    """
    serializer_class = SaccoJoinRequestSerializer
    permission_classes = [VehicleOwnerPermission]
    
    def get_queryset(self):
        return SaccoJoinRequest.objects.filter(
            owner=self.request.user
        ).select_related('vehicle', 'sacco', 'processed_by').prefetch_related('preferred_routes')
    
    def create(self, request, *args, **kwargs):
        try:
            # Get sacco_id and vehicle_id from request data
            sacco_id = request.data.get('sacco_id')
            vehicle_id = request.data.get('vehicle_id')
            
            if not sacco_id or not vehicle_id:
                return Response(
                    {'error': 'Both sacco_id and vehicle_id are required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get the sacco and vehicle
            sacco = get_object_or_404(Sacco, id=sacco_id)
            vehicle = get_object_or_404(Vehicle, id=vehicle_id, owner=request.user)
            
            # Check if vehicle already belongs to a sacco
            if vehicle.sacco:
                return Response(
                    {'error': 'Vehicle is already part of a sacco'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check if there's already a pending request
            existing_request = SaccoJoinRequest.objects.filter(
                vehicle=vehicle,
                sacco=sacco,
                status__in=['pending', 'under_review']
            ).first()
            
            if existing_request:
                return Response(
                    {'error': 'There is already a pending join request for this vehicle to this sacco'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check if vehicle has required documents
            required_docs = ['logbook', 'insurance', 'inspection', 'license', 'permit']
            missing_docs = []
            
            for doc_type in required_docs:
                if not VehicleDocument.objects.filter(
                    vehicle=vehicle,
                    document_type=doc_type
                ).exists():
                    missing_docs.append(doc_type)
            
            if missing_docs:
                return Response({
                    'error': 'Missing required documents',
                    'missing_documents': missing_docs,
                    'message': 'Please upload all required documents before submitting a join request'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Create the join request
            serializer = self.get_serializer(data=request.data)
            if serializer.is_valid():
                with transaction.atomic():
                    join_request = serializer.save(
                        vehicle=vehicle,
                        sacco=sacco,
                        owner=request.user
                    )
                    
                    # Send confirmation email to vehicle owner
                    logger.info(f"Sending confirmation email to owner: {request.user.email}")
                    email_sent_to_owner = SaccoEmailService.send_join_request_confirmation(join_request)
                    
                    # Send notification email to sacco admins
                    logger.info(f"Sending notification email to sacco admins for: {sacco.name}")
                    email_sent_to_admin = SaccoEmailService.send_admin_new_request_notification(join_request)
                    
                    response_data = {
                        'success': True,
                        'message': 'Join request submitted successfully',
                        'request_id': join_request.id,
                        'status': join_request.status,
                        'data': serializer.data,
                        'email_notifications': {
                            'owner_notified': email_sent_to_owner,
                            'admin_notified': email_sent_to_admin
                        }
                    }
                    
                    # Add warnings for failed emails
                    if not email_sent_to_owner:
                        response_data['email_notifications']['owner_warning'] = 'Failed to send confirmation email to owner'
                        logger.warning(f"Failed to send confirmation email to {request.user.email}")
                    
                    if not email_sent_to_admin:
                        response_data['email_notifications']['admin_warning'] = 'Failed to send notification email to sacco admin'
                        logger.warning(f"Failed to send admin notification for sacco {sacco.name}")
                    
                    return Response(response_data, status=status.HTTP_201_CREATED)
            
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Error creating join request: {str(e)}")
            return Response({
                'success': False,
                'error': 'An error occurred while processing your request. Please try again.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SaccoJoinRequestDetailView(generics.RetrieveAPIView):
    serializer_class = SaccoJoinRequestSerializer
    
    def get_queryset(self):
        return SaccoJoinRequest.objects.filter(
            owner=self.request.user
        ).select_related('vehicle', 'sacco', 'processed_by').prefetch_related('preferred_routes')


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def approve_sacco_request(request, request_id):
    """Approve a vehicle join request"""
    try:
        join_request = get_object_or_404(SaccoJoinRequest, id=request_id)
        
        # Check if request is still pending
        if join_request.status != 'pending':
            return Response({
                'success': False,
                'error': f'Request is already {join_request.status}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate the request data (optional additional data)
        serializer = ApproveRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Update the request status
        with transaction.atomic():
            join_request.status = 'approved'
            join_request.processed_by = request.user
            join_request.processed_at = timezone.now()
            join_request.admin_notes = serializer.validated_data.get('admin_notes', '')
            join_request.save()
            
            # Update the vehicle to be approved by sacco
            vehicle = join_request.vehicle
            vehicle.sacco = join_request.sacco
            vehicle.is_approved_by_sacco = True
            vehicle.date_joined_sacco = timezone.now()
            vehicle.save()
            
            # Send approval notification email
            logger.info(f"Sending approval email to: {join_request.owner.email}")
            email_sent = SaccoEmailService.send_approval_notification(join_request)
        
        response_data = {
            'success': True,
            'message': 'Request approved successfully',
            'data': SaccoJoinRequestSerializer(join_request).data,
            'email_sent': email_sent
        }
        
        if not email_sent:
            response_data['email_warning'] = 'Request approved but failed to send notification email'
            logger.warning(f"Failed to send approval email to {join_request.owner.email}")
        
        return Response(response_data)
        
    except SaccoJoinRequest.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Request not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error approving request: {str(e)}")
        return Response({
            'success': False,
            'error': 'An error occurred while processing the approval'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reject_sacco_request(request, request_id):
    """Reject a vehicle join request with reason"""
    try:
        join_request = get_object_or_404(SaccoJoinRequest, id=request_id)
        
        # Check if request is still pending
        if join_request.status != 'pending':
            return Response({
                'success': False,
                'error': f'Request is already {join_request.status}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get rejection reason from either field name for flexibility
        rejection_reason = (
            request.data.get('rejection_reason') or 
            request.data.get('reason') or 
            ''
        ).strip()
        
        if not rejection_reason:
            return Response({
                'success': False,
                'error': 'Rejection reason is required',
                'message': 'Please provide either "rejection_reason" or "reason" field'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        admin_notes = request.data.get('admin_notes', '')
        
        # Update the request status
        with transaction.atomic():
            join_request.status = 'rejected'
            join_request.processed_by = request.user
            join_request.processed_at = timezone.now()
            join_request.rejection_reason = rejection_reason
            join_request.admin_notes = admin_notes
            join_request.save()
            
            # Send rejection notification email
            try:
                email_sent = SaccoEmailService.send_rejection_notification(
                    join_request, 
                    join_request.rejection_reason
                )
            except Exception as email_error:
                logger.error(f"Email service error: {str(email_error)}")
                email_sent = False
        
        response_data = {
            'success': True,
            'message': 'Request rejected successfully',
            'data': SaccoJoinRequestSerializer(join_request).data,
            'email_sent': email_sent
        }
        
        if not email_sent:
            response_data['email_warning'] = 'Request rejected but failed to send notification email'
        
        return Response(response_data)
        
    except SaccoJoinRequest.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Request not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error rejecting request: {str(e)}")
        return Response({
            'success': False,
            'error': 'An error occurred while processing the rejection'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_sacco_requests(request, sacco_id):
    """Get all vehicle join requests for a specific sacco (pending, approved, rejected)"""
    try:
        sacco = get_object_or_404(Sacco, id=sacco_id)
        
        # Get status filter from query params
        status_filter = request.query_params.get('status', None)
        
        requests_query = SaccoJoinRequest.objects.filter(
            sacco=sacco
        ).select_related('vehicle', 'owner', 'sacco', 'processed_by')
        
        if status_filter:
            requests_query = requests_query.filter(status=status_filter)
        
        requests_query = requests_query.order_by('-requested_at')
        
        serializer = SaccoAdminJoinRequestSerializer(requests_query, many=True)
        
        return Response({
            'success': True,
            'data': serializer.data,
            'count': requests_query.count(),
            'filters': {
                'status': status_filter
            }
        })
        
    except Sacco.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Sacco not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_pending_sacco_requests(request, sacco_id):
    """Get all pending vehicle join requests for a specific sacco"""
    try:
        sacco = get_object_or_404(Sacco, id=sacco_id)
        
        pending_requests = SaccoJoinRequest.objects.filter(
            sacco=sacco,
            status='pending'
        ).select_related(
            'vehicle', 'owner', 'sacco'
        ).prefetch_related(
            'vehicle__documents',  # Prefetch vehicle documents
            'preferred_routes'
        ).order_by('-requested_at')
        
        serializer = SaccoAdminJoinRequestSerializer(pending_requests, many=True)
        
        return Response({
            'success': True,
            'data': serializer.data,
            'count': pending_requests.count()
        })
        
    except Sacco.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Sacco not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_join_request_detail(request, request_id):
    """Get detailed information about a specific join request"""
    try:
        join_request = get_object_or_404(
            SaccoJoinRequest.objects.select_related(
                'vehicle', 'owner', 'sacco', 'processed_by'
            ).prefetch_related(
                'vehicle__documents',  # Prefetch vehicle documents
                'preferred_routes'
            ),
            id=request_id
        )
        
        serializer = SaccoAdminJoinRequestSerializer(join_request)
        
        return Response({
            'success': True,
            'data': serializer.data
        })
        
    except SaccoJoinRequest.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Request not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
@api_view(['GET'])
@permission_classes([AllowAny])
def get_vehicle_documents(request, vehicle_id):
    try:
        # Verify the vehicle belongs to the user or they have permission to view it
        vehicle = get_object_or_404(Vehicle, id=vehicle_id)
        
        # Add permission check if needed
        if vehicle.owner != request.user:
            return Response({'error': 'Permission denied'}, status=403)
        
        documents = vehicle.documents.all()
        
        documents_data = []
        for doc in documents:
            documents_data.append({
                'id': doc.id,
                'document_type': doc.document_type,
                'document_type_display': doc.get_document_type_display(),
                'document_name': doc.document_name,
                'document_url': doc.document_file.url if doc.document_file else None,
                'is_verified': doc.is_verified,
                'expiry_date': doc.expiry_date.isoformat() if doc.expiry_date else None,
                'is_expired': doc.is_expired,
                'days_until_expiry': doc.days_until_expiry,
            })
        
        return Response({'documents': documents_data})
    except Exception as e:
        return Response({'error': str(e)}, status=500)