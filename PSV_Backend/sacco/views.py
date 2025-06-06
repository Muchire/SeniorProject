from rest_framework import generics, filters, permissions
from django_filters.rest_framework import DjangoFilterBackend
from sacco.models import Sacco, SaccoAdminRequest
from sacco.serializers import SaccoSerializer, SaccoAdminRequestSerializer
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import exceptions

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

class ApproveSaccoAdminView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, pk):
        req = get_object_or_404(SaccoAdminRequest, pk=pk)

        if req.is_approved:
            return Response({"detail": "Request already approved."}, status=status.HTTP_400_BAD_REQUEST)

        if req.sacco:
            sacco = req.sacco
        else:
            sacco = Sacco.objects.create(
                name=req.sacco_name,
                location=req.location,
                date_established=req.date_established,
                registration_number=req.registration_number,
                contact_number=req.contact_number,
                email=req.email,
                website=req.website,
                sacco_admin=req.user
            )
            req.sacco = sacco

        sacco.sacco_admin = req.user
        sacco.save()

        req.is_approved = True
        req.reviewed = True
        req.save()
        req.user.is_sacco_admin = True
        req.user.sacco_admin_requested = False
        req.user.save()

        return Response({"detail": "Sacco admin request approved."})

