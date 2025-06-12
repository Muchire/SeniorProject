from django.urls import path
from .views import (
    SaccoAdminDashboardView,
    SaccoAdminEditView,
    SaccoAdminRouteListView,
    SaccoAdminRouteDetailView,
    SaccoAdminPassengerReviewsView,
    SaccoAdminOwnerReviewsView,
    SaccoAdminAllReviewsView,
    SaccoAdminRouteWithStopsListView,
    SaccoAdminRouteWithStopsDetailView,
)

app_name = 'sacco_admin'

urlpatterns = [
    # Dashboard
    path('dashboard/', SaccoAdminDashboardView.as_view(), name='admin-dashboard'),
    
    # Sacco management
    path('sacco/edit/', SaccoAdminEditView.as_view(), name='sacco-edit'),
    
    # Route management (basic)
    path('routes/', SaccoAdminRouteListView.as_view(), name='admin-routes-list'),
    path('routes/<int:pk>/', SaccoAdminRouteDetailView.as_view(), name='admin-route-detail'),
    
    # Route management with stops
    path('routes-with-stops/', SaccoAdminRouteWithStopsListView.as_view(), name='admin-routes-with-stops-list'),
    path('routes-with-stops/<int:pk>/', SaccoAdminRouteWithStopsDetailView.as_view(), name='admin-route-with-stops-detail'),
    
    # Review management
    path('reviews/passenger/', SaccoAdminPassengerReviewsView.as_view(), name='admin-passenger-reviews'),
    path('reviews/owner/', SaccoAdminOwnerReviewsView.as_view(), name='admin-owner-reviews'),
    path('reviews/all/', SaccoAdminAllReviewsView.as_view(), name='admin-all-reviews'),
]
