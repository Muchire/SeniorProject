# Add this to your Django urls.py
from django.urls import path
from .views import (
    VehicleListCreateView, VehicleDetailView, VehicleDocumentView, VehicleDocumentDetailView,
    VehicleEarningsEstimationView, SaccoJoinRequestView, SaccoJoinRequestDetailView,
    VehicleTripView, VehiclePerformanceView, VehicleOwnerDashboardView,
    VehicleOwnerReviewsView, AvailableSaccosView, SaccoDetailsView,
    RouteListView, CreateOwnerReviewView, VehicleStatsView, SaccoSearchView,
    SaccoDashboardView, CompareSaccosView, VehicleDocumentUploadView,
    VehicleMaintenanceView, VehicleRevenueAnalyticsView, VehicleComparisonView,
    VehicleAlertView, VehicleExportDataView, approve_sacco_request, reject_sacco_request,
    get_pending_sacco_requests, get_all_sacco_requests, get_join_request_detail,
    get_vehicle_documents
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
    path('<int:vehicle_id>/documents/upload/', VehicleDocumentUploadView.as_view(), name='vehicle-document-upload'),
    
    path('documents/<int:vehicle_id>/', get_vehicle_documents, name='get_vehicle_documents'),
    
    # Vehicle Maintenance
    path('<int:vehicle_id>/maintenance/', VehicleMaintenanceView.as_view(), name='vehicle-maintenance'),
    
    # Vehicle Analytics
    path('<int:vehicle_id>/analytics/', VehicleRevenueAnalyticsView.as_view(), name='vehicle-analytics'),
    path('comparison/', VehicleComparisonView.as_view(), name='vehicle-comparison'),
    
    # Earnings Estimation
    path('<int:vehicle_id>/earnings/', VehicleEarningsEstimationView.as_view(), name='vehicle-earnings'),
    
    # SACCO Join Requests
    path('join-requests/', SaccoJoinRequestView.as_view(), name='join-requests'),
    path('<int:sacco_id>/join-requests/pending/', get_pending_sacco_requests, name='sacco_pending_requests'),
    path('join-requests/<int:pk>/', SaccoJoinRequestDetailView.as_view(), name='join-request-detail'),
    path('sacco/<int:sacco_id>/join-requests/', get_all_sacco_requests, name='sacco_all_requests'),
    path('sacco/<int:sacco_id>/join-requests/pending/', get_pending_sacco_requests, name='sacco_pending_requests'),
    
    # Individual request operations
    path('join-requests/<int:request_id>/', get_join_request_detail, name='join_request_detail'),
    path('join-requests/<int:request_id>/approve/', approve_sacco_request, name='approve_sacco_request'),
    path('join-requests/<int:request_id>/reject/', reject_sacco_request, name='reject_sacco_request'),
    
    # Trips and Performance
    path('<int:vehicle_id>/trips/', VehicleTripView.as_view(), name='vehicle-trips'),
    path('<int:vehicle_id>/performance/', VehiclePerformanceView.as_view(), name='vehicle-performance'),
    
    # SACCO Information
    path('saccos/', AvailableSaccosView.as_view(), name='available-saccos'),
    path('saccos/search/', SaccoSearchView.as_view(), name='search-saccos'),
    path('saccos/compare/', CompareSaccosView.as_view(), name='compare-saccos'),
    path('saccos/<int:sacco_id>/', SaccoDetailsView.as_view(), name='sacco-details'),
    path('saccos/<int:sacco_id>/dashboard/', SaccoDashboardView.as_view(), name='sacco-dashboard'),
    
    # Routes
    path('routes/', RouteListView.as_view(), name='routes-list'),
    
    # Reviews
    path('reviews/', VehicleOwnerReviewsView.as_view(), name='owner-reviews'),
    path('saccos/<int:sacco_id>/reviews/create/', CreateOwnerReviewView.as_view(), name='create-review'),
    
    # Alerts and Notifications
    path('alerts/', VehicleAlertView.as_view(), name='vehicle-alerts'),
    
    # Export Data
    path('export/', VehicleExportDataView.as_view(), name='export-data'),
]