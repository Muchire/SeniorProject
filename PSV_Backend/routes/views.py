from rest_framework import generics, filters
from rest_framework import permissions
from rest_framework.generics import ListAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from sacco.models import Sacco
from sacco.serializers import SaccoSerializer
from .models import Route
from .serializers import RouteSerializer



# List and create routes
class RouteListCreateView(generics.ListCreateAPIView):
    queryset = Route.objects.all().select_related('sacco').prefetch_related('stops')
    # permission_classes = [permissions.IsAuthenticated]
    serializer_class = RouteSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['start_location', 'end_location', 'sacco']
    search_fields = ['start_location', 'end_location', 'sacco__name']
    

# Show all routes for a given start location
class SaccosFromLocationView(ListAPIView):
    serializer_class = SaccoSerializer

    def get_queryset(self):
        location = self.kwargs['location']
        routes = Route.objects.filter(start_location__icontains=location)
        sacco_set  = {route.sacco for route in routes}
        return list(sacco_set)

# Search for saccos operating between two locations
class RouteSearchView(APIView):
    def get(self, request):
        start = request.query_params.get('from')
        end = request.query_params.get('to')

        if not start or not end:
            return Response({"error": "Please provide 'from' and 'to' query parameters"}, status=400)

        routes = Route.objects.filter(
            Q(start_location__icontains=start,end_location__icontains=end) |
            Q(start_location__icontains=end, end_location__icontains=start)
        ).select_related('sacco').prefetch_related('stops')

        serializer = RouteSerializer(routes, many=True)
        return Response(serializer.data)
