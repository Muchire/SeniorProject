from rest_framework import generics, filters, permissions
from django_filters.rest_framework import DjangoFilterBackend
from sacco.models import Sacco, SaccoAdminRequest
from routes.models import Route
from sacco.models import SaccoFinancialMetrics
from routes.serializers import RouteSerializer
from sacco.serializers import SaccoSerializer, SaccoAdminRequestSerializer,SaccoPOVSerializer
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from django.contrib.auth import get_user_model
from django.utils import timezone  # Added missing import

class SaccoListCreateView(generics.ListCreateAPIView):
    queryset = Sacco.objects.all()
    serializer_class = SaccoSerializer

    filter_backends = [DjangoFilterBackend,filters.SearchFilter]
    filterset_fields = ['name', 'location']
    search_fields = ['name', 'location']

class SaccoDetailView(APIView):
    queryset = Sacco.objects.all()
    serializer_class = SaccoSerializer

class SaccoDetailPOVView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Sacco.objects.all()
    serializer_class = SaccoPOVSerializer
class SaccoFinancialMetricsView(APIView):
    """
    Dedicated API for Sacco Financial Metrics
    GET: Retrieve financial metrics and route earnings
    POST/PUT: Update financial metrics (admin only)
    """
    
    def get(self, request, sacco_id):
        try:
            sacco = Sacco.objects.get(id=sacco_id)
            routes = Route.objects.filter(sacco=sacco)
            financial_metrics = SaccoFinancialMetrics.objects.get_or_create(sacco=sacco)[0]
            
            # Calculate route-specific earnings potential
            route_earnings = []
            for route in routes:
                daily_potential = route.fare * route.avg_daily_trips
                monthly_potential = daily_potential * 30
                
                # Factor in costs
                daily_fuel_cost = route.distance * 2 * route.fuel_cost_per_km  # round trip
                monthly_fuel_cost = daily_fuel_cost * 30
                monthly_maintenance = route.maintenance_cost_per_month
                
                # Sacco commission
                gross_monthly = monthly_potential
                commission = gross_monthly * (sacco.commission_rate / 100)
                net_monthly = gross_monthly - commission - monthly_fuel_cost - monthly_maintenance
                
                route_earnings.append({
                    'route_id': route.id,
                    'route_name': f"{route.start_location} - {route.end_location}",
                    'gross_monthly_potential': gross_monthly,
                    'net_monthly_potential': net_monthly,
                    'daily_trips': route.avg_daily_trips,
                    'fare_per_trip': route.fare,
                    'monthly_costs': monthly_fuel_cost + monthly_maintenance + commission,
                    'commission_rate': sacco.commission_rate,
                })
            
            return Response({
                'sacco_id': sacco.id,
                'sacco_name': sacco.name,
                'financial_metrics': {
                    'avg_monthly_revenue_per_vehicle': financial_metrics.avg_revenue_per_vehicle,
                    'operational_costs': financial_metrics.operational_costs,
                    'net_profit_margin': financial_metrics.net_profit_margin,
                    'owner_average_profit': financial_metrics.owner_average_profit,
                    'last_updated': financial_metrics.updated_at,
                },
                'route_earnings_potential': route_earnings,
                'total_routes': routes.count(),
                'calculated_at': timezone.now(),
            })
            
        except Sacco.DoesNotExist:
            return Response({'error': 'Sacco not found'}, status=404)
    
    def post(self, request, sacco_id):
        """Create or update financial metrics - Admin only"""
        if not self.has_sacco_admin_permission(request.user, sacco_id):
            return Response({'error': 'Permission denied. Sacco admin access required.'}, 
                          status=403)
        
        try:
            sacco = Sacco.objects.get(id=sacco_id)
            financial_metrics, created = SaccoFinancialMetrics.objects.get_or_create(sacco=sacco)
            
            # Update metrics with provided data
            financial_metrics.avg_revenue_per_vehicle = request.data.get(
                'avg_revenue_per_vehicle', financial_metrics.avg_revenue_per_vehicle
            )
            financial_metrics.operational_costs = request.data.get(
                'operational_costs', financial_metrics.operational_costs
            )
            financial_metrics.net_profit_margin = request.data.get(
                'net_profit_margin', financial_metrics.net_profit_margin
            )
            financial_metrics.owner_average_profit = request.data.get(
                'owner_average_profit', financial_metrics.owner_average_profit
            )
            
            financial_metrics.save()
            
            return Response({
                'message': 'Financial metrics updated successfully',
                'metrics': {
                    'avg_monthly_revenue_per_vehicle': financial_metrics.avg_revenue_per_vehicle,
                    'operational_costs': financial_metrics.operational_costs,
                    'net_profit_margin': financial_metrics.net_profit_margin,
                    'owner_average_profit': financial_metrics.owner_average_profit,
                    'updated_at': financial_metrics.updated_at,
                }
            })
            
        except Sacco.DoesNotExist:
            return Response({'error': 'Sacco not found'}, status=404)
        except Exception as e:
            return Response({'error': f'Failed to update metrics: {str(e)}'}, status=400)
    
    def put(self, request, sacco_id):
        """Update specific financial metrics - Admin only"""
        return self.post(request, sacco_id)  # Reuse POST logic
    
    def has_sacco_admin_permission(self, user, sacco_id):
        """
        Check if user has admin permission for this sacco
        Updated to work with your User model structure
        """
        if not user.is_authenticated:
            return False
            
        try:
            # Check if user is superuser (always has access)
            if user.is_superuser:
                return True
                
            # Check if user has sacco admin privileges
            if not user.is_sacco_admin:
                return False
                
            # Get the sacco to verify it exists
            sacco = Sacco.objects.get(id=sacco_id)
            
            # Option 1: If you have a sacco_admin field in Sacco model pointing to User
            if hasattr(sacco, 'sacco_admin') and sacco.sacco_admin == user:
                return True
                
            # Option 2: If you have a many-to-many admins field in Sacco model
            if hasattr(sacco, 'admins') and sacco.admins.filter(id=user.id).exists():
                return True
                
            # Option 3: For now, allow any user with is_sacco_admin=True to update any sacco
            # You can make this more restrictive later by adding specific sacco-user relationships
            return True
            
        except Sacco.DoesNotExist:
            return False
        except Exception as e:
            print(f"Permission check error: {e}")  # For debugging
            return False


class SaccoFinancialMetricsUpdateView(APIView):
    """
    Dedicated endpoint for batch financial metrics updates
    Useful for admin dashboards
    """
    
    def post(self, request):
        """Batch update multiple sacco financial metrics"""
        if not request.user.is_superuser:
            return Response({'error': 'Superuser access required'}, status=403)
        
        updates = request.data.get('updates', [])
        results = []
        
        for update in updates:
            sacco_id = update.get('sacco_id')
            metrics_data = update.get('metrics', {})
            
            try:
                sacco = Sacco.objects.get(id=sacco_id)
                financial_metrics, created = SaccoFinancialMetrics.objects.get_or_create(sacco=sacco)
                
                # Update metrics
                for field, value in metrics_data.items():
                    if hasattr(financial_metrics, field):
                        setattr(financial_metrics, field, value)
                
                financial_metrics.save()
                
                results.append({
                    'sacco_id': sacco_id,
                    'status': 'success',
                    'message': 'Updated successfully'
                })
                
            except Sacco.DoesNotExist:
                results.append({
                    'sacco_id': sacco_id,
                    'status': 'error',
                    'message': 'Sacco not found'
                })
            except Exception as e:
                results.append({
                    'sacco_id': sacco_id,
                    'status': 'error',
                    'message': str(e)
                })
        
        return Response({
            'batch_update_results': results,
            'total_processed': len(updates),
            'successful_updates': len([r for r in results if r['status'] == 'success'])
        })


# Alternative simplified version with basic admin check
class SaccoFinancialMetricsViewSimple(APIView):
    """
    Simplified version that just checks if user is_sacco_admin
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, sacco_id):
        try:
            sacco = Sacco.objects.get(id=sacco_id)
            routes = Route.objects.filter(sacco=sacco)
            financial_metrics = SaccoFinancialMetrics.objects.get_or_create(sacco=sacco)[0]
            
            # Calculate route-specific earnings potential
            route_earnings = []
            for route in routes:
                daily_potential = route.fare * route.avg_daily_trips
                monthly_potential = daily_potential * 30
                
                # Factor in costs
                daily_fuel_cost = route.distance * 2 * route.fuel_cost_per_km
                monthly_fuel_cost = daily_fuel_cost * 30
                monthly_maintenance = route.maintenance_cost_per_month
                
                # Sacco commission
                gross_monthly = monthly_potential
                commission = gross_monthly * (sacco.commission_rate / 100)
                net_monthly = gross_monthly - commission - monthly_fuel_cost - monthly_maintenance
                
                route_earnings.append({
                    'route_id': route.id,
                    'route_name': f"{route.start_location} - {route.end_location}",
                    'gross_monthly_potential': gross_monthly,
                    'net_monthly_potential': net_monthly,
                    'daily_trips': route.avg_daily_trips,
                    'fare_per_trip': route.fare,
                    'monthly_costs': monthly_fuel_cost + monthly_maintenance + commission,
                    'commission_rate': sacco.commission_rate,
                })
            
            return Response({
                'sacco_id': sacco.id,
                'sacco_name': sacco.name,
                'financial_metrics': {
                    'avg_monthly_revenue_per_vehicle': financial_metrics.avg_revenue_per_vehicle,
                    'operational_costs': financial_metrics.operational_costs,
                    'net_profit_margin': financial_metrics.net_profit_margin,
                    'owner_average_profit': financial_metrics.owner_average_profit,
                    'last_updated': financial_metrics.updated_at,
                },
                'route_earnings_potential': route_earnings,
                'total_routes': routes.count(),
                'calculated_at': timezone.now(),
            })
            
        except Sacco.DoesNotExist:
            return Response({'error': 'Sacco not found'}, status=404)
    
    def post(self, request, sacco_id):
        """Create or update financial metrics - Simple admin check"""
        # Simple check: user must be authenticated and have sacco admin privileges
        if not (request.user.is_superuser or request.user.is_sacco_admin):
            return Response({
                'error': 'Permission denied. Sacco admin access required.',
                'user_is_admin': request.user.is_sacco_admin,
                'user_is_superuser': request.user.is_superuser,
                'user_authenticated': request.user.is_authenticated
            }, status=403)
        
        try:
            sacco = Sacco.objects.get(id=sacco_id)
            financial_metrics, created = SaccoFinancialMetrics.objects.get_or_create(sacco=sacco)
            
            # Update metrics with provided data
            financial_metrics.avg_revenue_per_vehicle = request.data.get(
                'avg_revenue_per_vehicle', financial_metrics.avg_revenue_per_vehicle
            )
            financial_metrics.operational_costs = request.data.get(
                'operational_costs', financial_metrics.operational_costs
            )
            financial_metrics.net_profit_margin = request.data.get(
                'net_profit_margin', financial_metrics.net_profit_margin
            )
            financial_metrics.owner_average_profit = request.data.get(
                'owner_average_profit', financial_metrics.owner_average_profit
            )
            
            financial_metrics.save()
            
            return Response({
                'message': 'Financial metrics updated successfully',
                'created': created,
                'metrics': {
                    'avg_monthly_revenue_per_vehicle': financial_metrics.avg_revenue_per_vehicle,
                    'operational_costs': financial_metrics.operational_costs,
                    'net_profit_margin': financial_metrics.net_profit_margin,
                    'owner_average_profit': financial_metrics.owner_average_profit,
                    'updated_at': financial_metrics.updated_at,
                }
            })
            
        except Sacco.DoesNotExist:
            return Response({'error': 'Sacco not found'}, status=404)
        except Exception as e:
            return Response({'error': f'Failed to update metrics: {str(e)}'}, status=400)
    
    def put(self, request, sacco_id):
        """Update specific financial metrics"""
        return self.post(request, sacco_id)


class RequestSaccoAdminView(generics.CreateAPIView):
    serializer_class = SaccoAdminRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class SaccoAdminRequestListView(generics.ListAPIView):
    queryset = SaccoAdminRequest.objects.all()
    serializer_class = SaccoAdminRequestSerializer
    # permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        return self.queryset.filter(is_approved=False)

class ApproveSaccoAdminView(APIView):
    permission_classes = [permissions.IsAdminUser]

    @transaction.atomic
    def post(self, request, pk):
        try:
            req = get_object_or_404(SaccoAdminRequest, pk=pk)

            if req.is_approved:
                return Response({"detail": "Request already approved."}, status=status.HTTP_400_BAD_REQUEST)

            # Handle existing SACCO vs new SACCO
            if req.sacco:
                sacco = req.sacco
            else:
                # Validate required fields for new SACCO
                required_fields = {
                    'sacco_name': req.sacco_name,
                    'location': req.location,
                    'registration_number': req.registration_number,
                    'contact_number': req.contact_number,
                    'email': req.email,
                }
                
                missing_fields = [field for field, value in required_fields.items() if not value]
                if missing_fields:
                    return Response({
                        "detail": f"Missing required fields: {', '.join(missing_fields)}"
                    }, status=status.HTTP_400_BAD_REQUEST)

                # Create new SACCO
                try:
                    sacco = Sacco.objects.create(
                        name=req.sacco_name,
                        location=req.location,
                        date_established=req.date_established,
                        registration_number=req.registration_number,
                        contact_number=req.contact_number,
                        email=req.email,
                        website=req.website,
                    )
                    
                    # Link the new SACCO to the request
                    req.sacco = sacco
                    req.save()
                    
                except Exception as e:
                    return Response({
                        "detail": f"Failed to create SACCO: {str(e)}"
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # Assign the user as admin of the SACCO (if you have this field)
            try:
                if hasattr(sacco, 'sacco_admin'):
                    sacco.sacco_admin = req.user
                    sacco.save()
            except Exception as e:
                return Response({
                    "detail": f"Failed to assign admin to SACCO: {str(e)}"
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # Update user permissions
            try:
                user = get_user_model().objects.get(pk=req.user.pk)
                user.is_sacco_admin = True
                user.sacco_admin_requested = False
                user.save()
                
                # Verify the update
                user.refresh_from_db()
                
            except Exception as e:
                return Response({
                    "detail": f"Failed to update user permissions: {str(e)}"
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # Mark the request as approved and reviewed
            try:
                req.is_approved = True
                req.reviewed = True
                req.save()
            except Exception as e:
                return Response({
                    "detail": f"Failed to update request status: {str(e)}"
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # Verify everything was saved correctly
            sacco.refresh_from_db()
            req.refresh_from_db()
            user.refresh_from_db()

            return Response({
                "detail": "Sacco admin request approved successfully.",
                "sacco_id": sacco.id,
                "sacco_name": sacco.name,
                "user_is_admin": user.is_sacco_admin,
                "request_approved": req.is_approved,
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "detail": f"An error occurred during approval: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)