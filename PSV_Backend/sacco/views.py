from rest_framework import generics, filters, permissions
from django_filters.rest_framework import DjangoFilterBackend
from sacco.models import Sacco, SaccoAdminRequest
from sacco.serializers import SaccoSerializer, SaccoAdminRequestSerializer
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from django.contrib.auth import get_user_model

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
    # permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        return self.queryset.filter(is_approved=False)

class ApproveSaccoAdminView(APIView):
    permission_classes = [permissions.IsAdminUser]

    @transaction.atomic
    def post(self, request, pk):
        try:
            req = get_object_or_404(SaccoAdminRequest, pk=pk)

            if req.is_approved:
                return Response({"detail": "Request already approved."}, status=status.HTTP_400_BAD_REQUEST)

            # Handle existing SACCO vs new SACCO
            if req.sacco:
                sacco = req.sacco
            else:
                # Validate required fields for new SACCO
                required_fields = {
                    'sacco_name': req.sacco_name,
                    'location': req.location,
                    'registration_number': req.registration_number,
                    'contact_number': req.contact_number,
                    'email': req.email,
                }
                
                missing_fields = [field for field, value in required_fields.items() if not value]
                if missing_fields:
                    return Response({
                        "detail": f"Missing required fields: {', '.join(missing_fields)}"
                    }, status=status.HTTP_400_BAD_REQUEST)

                # Create new SACCO
                try:
                    sacco = Sacco.objects.create(
                        name=req.sacco_name,
                        location=req.location,
                        date_established=req.date_established,
                        registration_number=req.registration_number,
                        contact_number=req.contact_number,
                        email=req.email,
                        website=req.website,
                    )
                    
                    # Link the new SACCO to the request
                    req.sacco = sacco
                    req.save()
                    
                except Exception as e:
                    return Response({
                        "detail": f"Failed to create SACCO: {str(e)}"
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # Assign the user as admin of the SACCO (if you still need this field)
            try:
                sacco.sacco_admin = req.user
                sacco.save()
            except Exception as e:
                return Response({
                    "detail": f"Failed to assign admin to SACCO: {str(e)}"
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # Create SaccoAdmin instance - THIS IS THE KEY ADDITION
            try:
                sacco_admin, created = SaccoAdmin.objects.get_or_create(
                    user=req.user,
                    sacco=sacco,
                    defaults={
                        'approved_by': request.user,  # The admin who approved this request
                        'approved_at': timezone.now(),
                        'is_active': True,
                    }
                )
                
                if not created:
                    # If it already exists, just make sure it's active
                    sacco_admin.is_active = True
                    sacco_admin.approved_by = request.user
                    sacco_admin.approved_at = timezone.now()
                    sacco_admin.save()
                    
            except Exception as e:
                return Response({
                    "detail": f"Failed to create SaccoAdmin relationship: {str(e)}"
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # Update user permissions
            try:
                user = get_user_model().objects.get(pk=req.user.pk)
                user.is_sacco_admin = True
                user.sacco_admin_requested = False
                user.save()
                
                # Verify the update
                user.refresh_from_db()
                
            except Exception as e:
                return Response({
                    "detail": f"Failed to update user permissions: {str(e)}"
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # Mark the request as approved and reviewed
            try:
                req.is_approved = True
                req.reviewed = True
                req.save()
            except Exception as e:
                return Response({
                    "detail": f"Failed to update request status: {str(e)}"
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # Verify everything was saved correctly
            sacco.refresh_from_db()
            req.refresh_from_db()
            user.refresh_from_db()
            sacco_admin.refresh_from_db()

            return Response({
                "detail": "Sacco admin request approved successfully.",
                "sacco_id": sacco.id,
                "sacco_name": sacco.name,
                "user_is_admin": user.is_sacco_admin,
                "request_approved": req.is_approved,
                "sacco_admin_created": created,  # Let you know if it was newly created
                "has_sacco_admin_attr": hasattr(user, 'sacco_admin')  # Debug info
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "detail": f"An error occurred during approval: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)