# PSV_Backend/vehicles/urls.py
from django.urls import path
from .views import (
    VehicleListCreateView, VehicleDetailView, VehicleDocumentView, VehicleDocumentDetailView,
    VehicleEarningsEstimationView, SaccoJoinRequestView, SaccoJoinRequestDetailView,
    VehicleTripView, VehiclePerformanceView, VehicleOwnerDashboardView,
    VehicleOwnerReviewsView, AvailableSaccosView, SaccoDetailsView,
    RouteListView, CreateOwnerReviewView, VehicleStatsView
)

app_name = 'vehicles'

urlpatterns = [
    # Dashboard
    path('dashboard/', VehicleOwnerDashboardView.as_view(), name='owner-dashboard'),
    
    # Vehicle Management
    path('', VehicleListCreateView.as_view(), name='vehicle-list-create'),
    path('<int:pk>/', VehicleDetailView.as_view(), name='vehicle-detail'),
    path('<int:vehicle_id>/stats/', VehicleStatsView.as_view(), name='vehicle-stats'),
    
    # Vehicle Documents
    path('<int:vehicle_id>/documents/', VehicleDocumentView.as_view(), name='vehicle-documents'),
    path('<int:vehicle_id>/documents/<int:pk>/', VehicleDocumentDetailView.as_view(), name='vehicle-document-detail'),
    
    # Earnings Estimation
    path('<int:vehicle_id>/earnings/', VehicleEarningsEstimationView.as_view(), name='vehicle-earnings'),
    
    # SACCO Join Requests
    path('join-requests/', SaccoJoinRequestView.as_view(), name='join-requests'),
    path('join-requests/<int:pk>/', SaccoJoinRequestDetailView.as_view(), name='join-request-detail'),
    
    # Trips and Performance
    path('<int:vehicle_id>/trips/', VehicleTripView.as_view(), name='vehicle-trips'),
    path('<int:vehicle_id>/performance/', VehiclePerformanceView.as_view(), name='vehicle-performance'),
    
    # SACCO Information
    path('saccos/', AvailableSaccosView.as_view(), name='available-saccos'),
    path('saccos/<int:sacco_id>/', SaccoDetailsView.as_view(), name='sacco-details'),
    
    # Routes
    path('routes/', RouteListView.as_view(), name='routes-list'),
    
    # Reviews
    path('reviews/', VehicleOwnerReviewsView.as_view(), name='owner-reviews'),
    path('reviews/create/', CreateOwnerReviewView.as_view(), name='create-review'),
]