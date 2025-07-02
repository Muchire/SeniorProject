from django.urls import path
from .views import (
    RouteListCreateView,
    SaccosFromLocationView,
    RouteSearchView,
    RoutesBySaccoView,
    RouteDetailView,
    RouteFinancialUpdateView,
    SaccoRoutesFinancialBulkUpdateView,
    RouteEarningsCalculatorView,
)

urlpatterns = [
    # Basic route operations
    path('', RouteListCreateView.as_view(), name='route-list-create'),
    path('from/<str:location>/', SaccosFromLocationView.as_view(), name='saccos-from-location'),
    path('search-routes/', RouteSearchView.as_view(), name='route-search'),
    path('sacco/<int:sacco_id>/', RoutesBySaccoView.as_view(), name='routes-by-sacco'),
    path('<int:id>/', RouteDetailView.as_view(), name='route-detail'),
    
    # Financial management endpoints (Sacco Admin only)
    path('<int:id>/financial/', RouteFinancialUpdateView.as_view(), name='route-financial-update'),
    path('sacco/<int:sacco_id>/bulk-financial-update/', SaccoRoutesFinancialBulkUpdateView.as_view(), name='sacco-routes-bulk-financial-update'),
    
    # Earnings calculator (Public)
    path('<int:id>/earnings/', RouteEarningsCalculatorView.as_view(), name='route-earnings-calculator'),
]