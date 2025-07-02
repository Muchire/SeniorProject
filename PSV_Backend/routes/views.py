from rest_framework import generics, filters
from rest_framework import permissions
from rest_framework.generics import ListAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from sacco.models import Sacco
from sacco.serializers import SaccoSerializer
from .models import Route
from .serializers import RouteSerializer

class RouteListCreateView(generics.ListCreateAPIView):
    queryset = Route.objects.all().select_related('sacco').prefetch_related('stops')
    serializer_class = RouteSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['start_location', 'end_location', 'sacco']
    search_fields = ['start_location', 'end_location', 'sacco__name']
    
    def perform_create(self, serializer):
        """Add financial data when creating a route"""
        route = serializer.save()
        
        # Set default financial values if not provided
        if not route.avg_daily_trips:
            route.avg_daily_trips = 8  # Default: 8 trips per day
        if not route.fuel_cost_per_km:
            route.fuel_cost_per_km = 12.00  # Default: 12 KES per km
        if not route.maintenance_cost_per_month:
            route.maintenance_cost_per_month = 15000.00  # Default: 15k KES per month
        if not route.peak_hours_multiplier:
            route.peak_hours_multiplier = 1.5  # 50% more during peak hours
        if not route.seasonal_variance:
            route.seasonal_variance = 1.2  # 20% seasonal variation
            
        # Calculate average monthly revenue based on fare and trips
        if not route.avg_monthly_revenue:
            daily_revenue = route.fare * route.avg_daily_trips
            route.avg_monthly_revenue = daily_revenue * 30
            
        route.save()

class SaccosFromLocationView(ListAPIView):
    serializer_class = SaccoSerializer

    def get_queryset(self):
        location = self.kwargs['location']
        routes = Route.objects.filter(start_location__icontains=location)
        sacco_set = {route.sacco for route in routes}
        return list(sacco_set)

class RouteSearchView(APIView):
    def get(self, request):
        start = request.query_params.get('from')
        end = request.query_params.get('to')

        if not start or not end:
            return Response({"error": "Please provide 'from' and 'to' query parameters"}, status=400)

        routes = Route.objects.filter(
            Q(start_location__icontains=start, end_location__icontains=end) |
            Q(start_location__icontains=end, end_location__icontains=start)
        ).select_related('sacco').prefetch_related('stops')

        serializer = RouteSerializer(routes, many=True)
        return Response(serializer.data)

class RoutesBySaccoView(ListAPIView):
    serializer_class = RouteSerializer

    def get_queryset(self):
        sacco_id = self.kwargs.get('sacco_id')
        return Route.objects.filter(sacco_id=sacco_id).select_related('sacco').prefetch_related('stops')

class RouteDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Route.objects.all().select_related('sacco').prefetch_related('stops')
    serializer_class = RouteSerializer
    lookup_field = 'id'
    
    def get_permissions(self):
        """
        Different permissions for different actions:
        - GET: Anyone can view
        - PUT/PATCH/DELETE: Only sacco admins for their routes
        """
        if self.request.method == 'GET':
            return [permissions.AllowAny()]
        else:
            return [permissions.IsAuthenticated()]
    
    def check_sacco_admin_permission(self, route):
        """Check if user has admin permission for this route's sacco"""
        user = self.request.user
        
        if not user.is_authenticated:
            return False
            
        # Superuser always has access
        if user.is_superuser:
            return True
            
        # Check if user has sacco admin privileges
        if not user.is_sacco_admin:
            return False
            
        # For now, allow any sacco admin to edit any route
        # You can make this more restrictive by checking specific sacco ownership
        return True
    
    def update(self, request, *args, **kwargs):
        route = self.get_object()
        
        if not self.check_sacco_admin_permission(route):
            return Response({
                'error': 'Permission denied. Sacco admin access required.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Allow partial updates
        partial = kwargs.pop('partial', True)
        serializer = self.get_serializer(route, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        # Before saving, recalculate monthly revenue if relevant fields changed
        if 'avg_daily_trips' in request.data or 'fare' in request.data:
            route = serializer.save()
            if route.avg_daily_trips and route.fare:
                daily_revenue = route.fare * route.avg_daily_trips
                route.avg_monthly_revenue = daily_revenue * 30
                route.save()
        else:
            route = serializer.save()
        
        return Response({
            'message': 'Route updated successfully',
            'route': RouteSerializer(route).data
        })
    
    def destroy(self, request, *args, **kwargs):
        route = self.get_object()
        
        if not self.check_sacco_admin_permission(route):
            return Response({
                'error': 'Permission denied. Sacco admin access required.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        route_name = f"{route.start_location} - {route.end_location}"
        route.delete()
        
        return Response({
            'message': f'Route "{route_name}" deleted successfully'
        }, status=status.HTTP_204_NO_CONTENT)

class RouteFinancialUpdateView(APIView):
    """
    Dedicated endpoint for updating route financial data
    Only accessible by sacco admins
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def check_sacco_admin_permission(self, route):
        """Check if user has admin permission for this route's sacco"""
        user = self.request.user
        
        if user.is_superuser:
            return True
            
        if not user.is_sacco_admin:
            return False
            
        # For now, allow any sacco admin to edit any route
        # You can make this more restrictive later
        return True
    
    def patch(self, request, id):
        """Update only financial fields of a route"""
        try:
            route = Route.objects.get(id=id)
        except Route.DoesNotExist:
            return Response({'error': 'Route not found'}, status=status.HTTP_404_NOT_FOUND)
        
        if not self.check_sacco_admin_permission(route):
            return Response({
                'error': 'Permission denied. Sacco admin access required.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Financial fields that can be updated
        financial_fields = [
            'avg_daily_trips', 'peak_hours_multiplier', 'seasonal_variance',
            'fuel_cost_per_km', 'maintenance_cost_per_month'
        ]
        
        updated_fields = {}
        for field in financial_fields:
            if field in request.data:
                setattr(route, field, request.data[field])
                updated_fields[field] = request.data[field]
        
        # Also allow updating fare since it affects revenue
        if 'fare' in request.data:
            route.fare = request.data['fare']
            updated_fields['fare'] = request.data['fare']
        
        # Recalculate monthly revenue if trips or fare changed
        if 'avg_daily_trips' in updated_fields or 'fare' in updated_fields:
            if route.avg_daily_trips and route.fare:
                daily_revenue = route.fare * route.avg_daily_trips
                route.avg_monthly_revenue = daily_revenue * 30
                updated_fields['avg_monthly_revenue'] = route.avg_monthly_revenue
        
        route.save()
        
        return Response({
            'message': 'Route financial data updated successfully',
            'route_id': route.id,
            'route_name': f"{route.start_location} - {route.end_location}",
            'updated_fields': updated_fields,
            'calculated_monthly_revenue': route.avg_monthly_revenue
        })

class SaccoRoutesFinancialBulkUpdateView(APIView):
    """
    Bulk update financial data for all routes of a specific sacco
    Only accessible by sacco admins
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def check_sacco_admin_permission(self, user):
        """Check if user has sacco admin privileges"""
        return user.is_superuser or user.is_sacco_admin
    
    def post(self, request, sacco_id):
        """Bulk update financial data for all routes of a sacco"""
        if not self.check_sacco_admin_permission(request.user):
            return Response({
                'error': 'Permission denied. Sacco admin access required.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        try:
            sacco = Sacco.objects.get(id=sacco_id)
        except Sacco.DoesNotExist:
            return Response({'error': 'Sacco not found'}, status=status.HTTP_404_NOT_FOUND)
        
        routes = Route.objects.filter(sacco=sacco)
        financial_data = request.data.get('financial_data', {})
        
        if not financial_data:
            return Response({
                'error': 'No financial data provided'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        updated_routes = []
        
        for route in routes:
            updated_fields = {}
            
            # Update financial fields
            financial_fields = [
                'avg_daily_trips', 'peak_hours_multiplier', 'seasonal_variance',
                'fuel_cost_per_km', 'maintenance_cost_per_month'
            ]
            
            for field in financial_fields:
                if field in financial_data:
                    setattr(route, field, financial_data[field])
                    updated_fields[field] = financial_data[field]
            
            # Recalculate monthly revenue
            if route.avg_daily_trips and route.fare:
                daily_revenue = route.fare * route.avg_daily_trips
                route.avg_monthly_revenue = daily_revenue * 30
                updated_fields['calculated_monthly_revenue'] = route.avg_monthly_revenue
            
            route.save()
            
            updated_routes.append({
                'route_id': route.id,
                'route_name': f"{route.start_location} - {route.end_location}",
                'updated_fields': updated_fields
            })
        
        return Response({
            'message': f'Financial data updated for {len(updated_routes)} routes in {sacco.name}',
            'sacco_id': sacco_id,
            'sacco_name': sacco.name,
            'updated_routes': updated_routes,
            'total_routes_updated': len(updated_routes)
        })

class RouteEarningsCalculatorView(APIView):
    """
    Calculate earnings potential for a specific route
    Accessible to anyone
    """
    def get(self, request, id):
        """Get detailed earnings calculation for a route"""
        try:
            route = Route.objects.select_related('sacco').get(id=id)
        except Route.DoesNotExist:
            return Response({'error': 'Route not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Basic calculations
        daily_potential = route.fare * (route.avg_daily_trips or 0)
        monthly_potential = daily_potential * 30
        
        # Cost calculations
        daily_fuel_cost = (route.distance * 2) * (route.fuel_cost_per_km or 0)  # round trip
        monthly_fuel_cost = daily_fuel_cost * 30
        monthly_maintenance = route.maintenance_cost_per_month or 0
        
        # Sacco commission
        gross_monthly = monthly_potential
        commission = gross_monthly * (route.sacco.commission_rate / 100) if hasattr(route.sacco, 'commission_rate') else 0
        
        # Net calculations
        total_monthly_costs = monthly_fuel_cost + monthly_maintenance + commission
        net_monthly = gross_monthly - total_monthly_costs
        
        # Peak hours and seasonal adjustments
        peak_adjusted = net_monthly * (route.peak_hours_multiplier or 1)
        seasonal_adjusted = peak_adjusted * (route.seasonal_variance or 1)
        
        return Response({
            'route_id': route.id,
            'route_name': f"{route.start_location} - {route.end_location}",
            'sacco': route.sacco.name,
            'earnings_breakdown': {
                'basic_calculations': {
                    'fare_per_trip': route.fare,
                    'daily_trips': route.avg_daily_trips,
                    'daily_potential': daily_potential,
                    'monthly_potential': monthly_potential,
                },
                'cost_breakdown': {
                    'daily_fuel_cost': daily_fuel_cost,
                    'monthly_fuel_cost': monthly_fuel_cost,
                    'monthly_maintenance': monthly_maintenance,
                    'sacco_commission': commission,
                    'total_monthly_costs': total_monthly_costs,
                },
                'net_earnings': {
                    'basic_monthly_net': net_monthly,
                    'peak_hours_adjusted': peak_adjusted,
                    'seasonal_adjusted': seasonal_adjusted,
                },
                'multipliers': {
                    'peak_hours_multiplier': route.peak_hours_multiplier,
                    'seasonal_variance': route.seasonal_variance,
                }
            },
            'calculated_at': route.updated_at if hasattr(route, 'updated_at') else None
        })