# PSV_Backend/vehicles/urls.py
from django.urls import path
from .views import (
    VehicleListCreateView, VehicleDetailView, VehicleDocumentView, VehicleDocumentDetailView,
    VehicleEarningsEstimationView, SaccoJoinRequestView, SaccoJoinRequestDetailView,
    VehicleTripView, VehiclePerformanceView, VehicleOwnerDashboardView,
    VehicleOwnerReviewsView, AvailableSaccosView, SaccoDetailsView,
    RouteListView, CreateOwnerReviewView, VehicleStatsView, SaccoDetailedDashboardView,
    SaccoDashboardSearchView, SaccoComparisonView)
from .views import (
    SaccoJoinRequestCreateView, VehicleJoinRequestListView,
    VehicleJoinRequestDetailView, VehicleDocumentUploadView,
    VehicleDocumentListView, VehicleDocumentStatusView
)


urlpatterns = [
    # Dashboard
    path('dashboard/', VehicleOwnerDashboardView.as_view(), name='owner-dashboard'),
    
    # Vehicle Management
    path('', VehicleListCreateView.as_view(), name='vehicle-list-create'),
    path('<int:pk>/', VehicleDetailView.as_view(), name='vehicle-detail'),
    path('<int:vehicle_id>/stats/', VehicleStatsView.as_view(), name='vehicle-stats'),
    
    # Vehicle Documents (Enhanced)
    path('<int:vehicle_id>/documents/', VehicleDocumentView.as_view(), name='vehicle-documents'),
    path('<int:vehicle_id>/documents/<int:pk>/', VehicleDocumentDetailView.as_view(), name='vehicle-document-detail'),
    
    # NEW: Enhanced Document Management for Sacco Joining
    path('<int:vehicle_id>/documents/list/', VehicleDocumentListView.as_view(), name='vehicle-documents-list'),
    path('<int:vehicle_id>/documents/upload/', VehicleDocumentUploadView.as_view(), name='vehicle-document-upload'),
    path('<int:vehicle_id>/documents/status/', VehicleDocumentStatusView.as_view(), name='vehicle-document-status'),
    
    # Earnings Estimation
    path('<int:vehicle_id>/earnings/', VehicleEarningsEstimationView.as_view(), name='vehicle-earnings'),
    
    # SACCO Join Requests (Enhanced)
    path('join-requests/', SaccoJoinRequestView.as_view(), name='join-requests'),
    path('join-requests/<int:pk>/', SaccoJoinRequestDetailView.as_view(), name='join-request-detail'),
    
    # NEW: Specific Sacco Join Request Creation
    path('sacco/<int:sacco_id>/join/<int:vehicle_id>/', 
         SaccoJoinRequestCreateView.as_view(), 
         name='sacco-join-request-create'),
    
    # NEW: Vehicle-specific Join Requests
    path('vehicle-join-requests/', 
         VehicleJoinRequestListView.as_view(), 
         name='vehicle-join-requests-list'),
    
    path('vehicle-join-requests/<int:pk>/', 
         VehicleJoinRequestDetailView.as_view(), 
         name='vehicle-join-request-detail'),
    
    # Trips and Performance
    path('<int:vehicle_id>/trips/', VehicleTripView.as_view(), name='vehicle-trips'),
    path('<int:vehicle_id>/performance/', VehiclePerformanceView.as_view(), name='vehicle-performance'),
    
    # SACCO Information - SPECIFIC PATTERNS FIRST
    path('saccos/search/', SaccoDashboardSearchView.as_view(), name='sacco-dashboard-search'),
    path('saccos/compare/', SaccoComparisonView.as_view(), name='sacco-comparison'),
    path('saccos/', AvailableSaccosView.as_view(), name='available-saccos'),
    path('saccos/<int:sacco_id>/dashboard/', SaccoDetailedDashboardView.as_view(), name='sacco-detailed-dashboard'),
    path('saccos/<int:sacco_id>/reviews/create/', CreateOwnerReviewView.as_view(), name='create-sacco-review'),
    path('saccos/<int:sacco_id>/', SaccoDetailsView.as_view(), name='sacco-details'),
    
    # Routes
    path('routes/', RouteListView.as_view(), name='routes-list'),
    
    # Reviews
    path('reviews/', VehicleOwnerReviewsView.as_view(), name='owner-reviews'),
]