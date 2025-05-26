from rest_framework import generics, filters
from django_filters.rest_framework import DjangoFilterBackend
from sacco.models import Sacco
from sacco.serializers import SaccoSerializer

class SaccoListCreateView(generics.ListCreateAPIView):
    queryset = Sacco.objects.all()
    serializer_class = SaccoSerializer


    filter_backends = [DjangoFilterBackend,filters.SearchFilter]
    filterset_fields = ['name', 'location']
    search_fields = ['name', 'location']

class SaccoDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Sacco.objects.all()
    serializer_class = SaccoSerializer
