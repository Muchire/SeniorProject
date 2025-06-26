# PSV_Backend/vehicles/views.py
from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count, Avg, Sum
from django.utils import timezone
from .serializers import (
    EnhancedSaccoDashboardSerializer, VehicleSerializer, VehicleDocumentSerializer, SaccoJoinRequestSerializer,
    VehicleTripSerializer, VehiclePerformanceSerializer,
    VehicleOwnerDashboardSerializer, VehicleOwnerReviewsSerializer,
)
from reviews.serializers import OwnerReviewSerializer
from routes.models import Route
from sacco.models import Sacco
from reviews.models import OwnerReview
from .models import Vehicle, VehicleDocument, SaccoJoinRequest, VehicleTrip, VehiclePerformance



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
    permission_classes = [VehicleOwnerPermission]
    
    def get_queryset(self):
        return Vehicle.objects.filter(owner=self.request.user).order_by('-created_at')
    
    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


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


class SaccoJoinRequestCreateView(APIView):
    """
    Create a join request for a specific sacco
    """
    permission_classes = [VehicleOwnerPermission]
    
    def post(self, request, sacco_id, vehicle_id):
        try:
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
            serializer = SaccoJoinRequestSerializer(data=request.data)
            if serializer.is_valid():
                with transaction.atomic():
                    join_request = serializer.save(
                        vehicle=vehicle,
                        sacco=sacco,
                        owner=request.user
                    )
                
                return Response({
                    'message': 'Join request submitted successfully',
                    'request_id': join_request.id,
                    'status': join_request.status
                }, status=status.HTTP_201_CREATED)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SaccoJoinRequestDetailView(generics.RetrieveAPIView):
    serializer_class = SaccoJoinRequestSerializer
    permission_classes = [VehicleOwnerPermission]
    
    def get_queryset(self):
        return SaccoJoinRequest.objects.filter(owner=self.request.user)


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
    serializer_class = OwnerReviewSerializer  # ✅ Use the correct one

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
    
class SaccoDashboardSearchView(APIView):
    """Enhanced sacco search with complete dashboard information"""
    permission_classes = [VehicleOwnerPermission]
    
    def get(self, request):
        # Search parameters
        search_query = request.query_params.get('search', '')
        route_filter = request.query_params.get('route', '')
        location_filter = request.query_params.get('location', '')
        min_rating = request.query_params.get('min_rating', 0)
        
        # Start with all saccos
        saccos = Sacco.objects.all()
        
        # Apply filters
        if search_query:
            saccos = saccos.filter(
                Q(name__icontains=search_query) |
                Q(location__icontains=search_query)
            )
        
        if route_filter:
            saccos = saccos.filter(
                Q(routes__start_location__icontains=route_filter) |
                Q(routes__end_location__icontains=route_filter)
            ).distinct()
        
        if location_filter:
            saccos = saccos.filter(location__icontains=location_filter)
        
        # Add rating filter
        if float(min_rating) > 0:
            saccos = saccos.annotate(
                avg_rating=Avg('owner_reviews__average')
            ).filter(avg_rating__gte=float(min_rating))
        
        # Add basic stats for listing
        saccos = saccos.annotate(
            total_vehicles=Count('vehicles'),
            active_vehicles=Count('vehicles', filter=Q(vehicles__is_active=True)),
            total_routes=Count('routes'),
            avg_rating=Avg('owner_reviews__average'),
            total_reviews=Count('owner_reviews')
        ).order_by('-avg_rating', '-total_vehicles')
        
        # Serialize the results
        results = []
        for sacco in saccos:
            results.append({
                'id': sacco.id,
                'name': sacco.name,
                'location': sacco.location,
                'total_vehicles': sacco.total_vehicles,
                'active_vehicles': sacco.active_vehicles,
                'total_routes': sacco.total_routes,
                'avg_rating': float(sacco.avg_rating or 0),
                'total_reviews': sacco.total_reviews,
                'contact_number': sacco.contact_number,
                'email': sacco.email
            })
        
        return Response({
            'results': results,
            'total_count': len(results),
            'search_params': {
                'search': search_query,
                'route': route_filter,
                'location': location_filter,
                'min_rating': min_rating
            }
        })


class SaccoDetailedDashboardView(APIView):
    """Get complete detailed dashboard for a specific sacco"""
    permission_classes = [VehicleOwnerPermission]
    
    def get(self, request, sacco_id):
        sacco = get_object_or_404(Sacco, id=sacco_id)
        
        # Use the enhanced serializer
        serializer = EnhancedSaccoDashboardSerializer(sacco)
        
        return Response(serializer.data)


class SaccoComparisonView(APIView):
    """Compare multiple saccos side by side"""
    permission_classes = [VehicleOwnerPermission]
    
    def post(self, request):
        sacco_ids = request.data.get('sacco_ids', [])
        
        if not sacco_ids or len(sacco_ids) > 5:  # Limit to 5 saccos
            return Response(
                {'error': 'Please provide 1-5 sacco IDs for comparison'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        saccos = Sacco.objects.filter(id__in=sacco_ids)
        comparison_data = []
        
        for sacco in saccos:
            # Get summary data for comparison
            vehicles = Vehicle.objects.filter(sacco=sacco, is_active=True)
            routes = Route.objects.filter(sacco=sacco)
            reviews = OwnerReview.objects.filter(sacco=sacco)
            
            # Calculate average earnings
            total_earnings = 0
            vehicle_count = vehicles.count()
            
            if vehicle_count > 0:
                for vehicle in vehicles:
                    best_earnings = 0
                    for route in routes:
                        earnings = vehicle.calculate_monthly_earnings(route)
                        if earnings['net_earnings'] > best_earnings:
                            best_earnings = earnings['net_earnings']
                    total_earnings += best_earnings
                
                avg_earnings_per_vehicle = total_earnings / vehicle_count
            else:
                avg_earnings_per_vehicle = 0
            
            # Ratings summary
            ratings = reviews.aggregate(
                avg_rating=Avg('average'),
                avg_payment_punctuality=Avg('payment_punctuality'),
                avg_rate_fairness=Avg('rate_fairness'),
                avg_support=Avg('support'),
                total_reviews=Count('id')
            )
            
            comparison_data.append({
                'id': sacco.id,
                'name': sacco.name,
                'location': sacco.location,
                'total_vehicles': vehicle_count,
                'total_routes': routes.count(),
                'avg_rating': float(ratings['avg_rating'] or 0),
                'total_reviews': ratings['total_reviews'],
                'avg_payment_punctuality': float(ratings['avg_payment_punctuality'] or 0),
                'avg_rate_fairness': float(ratings['avg_rate_fairness'] or 0),
                'avg_support': float(ratings['avg_support'] or 0),
                'avg_earnings_per_vehicle': avg_earnings_per_vehicle,
                'total_estimated_monthly_revenue': total_earnings,
                'contact_info': {
                    'phone': sacco.contact_number,
                    'email': sacco.email,
                    'website': sacco.website
                }
            })
        
        return Response({
            'comparison': comparison_data,
            'comparison_summary': {
                'highest_rated': max(comparison_data, key=lambda x: x['avg_rating'])['name'],
                'most_vehicles': max(comparison_data, key=lambda x: x['total_vehicles'])['name'],
                'best_earnings': max(comparison_data, key=lambda x: x['avg_earnings_per_vehicle'])['name'],
                'most_routes': max(comparison_data, key=lambda x: x['total_routes'])['name']
            }
        })
class VehicleJoinRequestListView(generics.ListAPIView):
    """
    List all join requests for the authenticated user's vehicles
    """
    serializer_class = SaccoJoinRequestSerializer
    permission_classes = [VehicleOwnerPermission]
    
    def get_queryset(self):
        return SaccoJoinRequest.objects.filter(
            owner=self.request.user
        ).select_related('vehicle', 'sacco', 'processed_by').prefetch_related('preferred_routes')


class VehicleJoinRequestDetailView(generics.RetrieveAPIView):
    """
    Get details of a specific join request
    """
    serializer_class = SaccoJoinRequestSerializer
    permission_classes = [VehicleOwnerPermission]
    
    def get_queryset(self):
        return SaccoJoinRequest.objects.filter(
            owner=self.request.user
        ).select_related('vehicle', 'sacco', 'processed_by').prefetch_related('preferred_routes')


class VehicleDocumentUploadView(APIView):
    """
    Upload documents for a vehicle
    """
    permission_classes = [VehicleOwnerPermission]
    
    def post(self, request, vehicle_id):
        try:
            vehicle = get_object_or_404(Vehicle, id=vehicle_id, owner=request.user)
            
            serializer = VehicleDocumentSerializer(data=request.data)
            if serializer.is_valid():
                # Check if document type already exists for this vehicle
                document_type = serializer.validated_data['document_type']
                existing_doc = VehicleDocument.objects.filter(
                    vehicle=vehicle,
                    document_type=document_type
                ).first()
                
                if existing_doc:
                    # Update existing document
                    serializer = VehicleDocumentSerializer(
                        existing_doc, 
                        data=request.data, 
                        partial=True
                    )
                    if serializer.is_valid():
                        serializer.save()
                        return Response({
                            'message': 'Document updated successfully',
                            'document': serializer.data
                        }, status=status.HTTP_200_OK)
                else:
                    # Create new document
                    document = serializer.save(vehicle=vehicle)
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


class VehicleDocumentListView(generics.ListAPIView):
    """
    List all documents for a specific vehicle
    """
    serializer_class = VehicleDocumentSerializer
    permission_classes = [VehicleOwnerPermission]
    
    def get_queryset(self):
        vehicle_id = self.kwargs['vehicle_id']
        vehicle = get_object_or_404(Vehicle, id=vehicle_id, owner=self.request.user)
        return VehicleDocument.objects.filter(vehicle=vehicle)


class VehicleDocumentStatusView(APIView):
    """
    Check document completion status for a vehicle
    """
    permission_classes = [VehicleOwnerPermission]
    
    def get(self, request, vehicle_id):
        try:
            vehicle = get_object_or_404(Vehicle, id=vehicle_id, owner=request.user)
            
            required_docs = ['logbook', 'insurance', 'inspection', 'license', 'permit']
            uploaded_docs = VehicleDocument.objects.filter(
                vehicle=vehicle
            ).values_list('document_type', flat=True)
            
            status_data = {
                'vehicle_id': vehicle.id,
                'vehicle_registration': vehicle.registration_number,
                'required_documents': required_docs,
                'uploaded_documents': list(uploaded_docs),
                'missing_documents': [doc for doc in required_docs if doc not in uploaded_docs],
                'is_complete': all(doc in uploaded_docs for doc in required_docs),
                'completion_percentage': round((len(uploaded_docs) / len(required_docs)) * 100, 2)
            }
            
            return Response(status_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )