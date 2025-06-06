from django.urls import path
from .views import (
    RouteListCreateView,
    SaccosFromLocationView,
    RouteSearchView,
)

urlpatterns = [
    path('', RouteListCreateView.as_view(), name='route-list-create'),
    path('from/<str:location>/', SaccosFromLocationView.as_view(), name='saccos-from-location'),
    path('search-routes/', RouteSearchView.as_view(), name='route-search'),
]
