from rest_framework import generics, filters, permissions
from django_filters.rest_framework import DjangoFilterBackend
from sacco.models import Sacco, SaccoAdminRequest
from sacco.serializers import SaccoSerializer, SaccoAdminRequestSerializer

class SaccoListCreateView(generics.ListCreateAPIView):
    queryset = Sacco.objects.all()
    serializer_class = SaccoSerializer


    filter_backends = [DjangoFilterBackend,filters.SearchFilter]
    filterset_fields = ['name', 'location']
    search_fields = ['name', 'location']

class SaccoDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Sacco.objects.all()
    serializer_class = SaccoSerializer
class RequestSaccoAdminView(generics.CreateAPIView):
    serializer_class = SaccoAdminRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class SaccoAdminRequestListView(generics.ListAPIView):
    queryset = SaccoAdminRequest.objects.all()
    serializer_class = SaccoAdminRequestSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        return self.queryset.filter(is_approved=False)

class ApproveSaccoAdminView(generics.UpdateAPIView):
    queryset = SaccoAdminRequest.objects.all()
    serializer_class = SaccoAdminRequestSerializer
    permission_classes = [permissions.IsAdminUser]

    def perform_update(self, serializer):
        instance = serializer.save(approved=True)
        Sacco.objects.create(
            name=instance.sacco_name,
            sacco_admin=instance.user
        )
        if instance.is_approved:
            instance.user.is_staff = True  
            instance.user.save()

