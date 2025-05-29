from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.models import Token
# from .models import User
from .serializers import (
    RegisterSerializer, LoginSerializer,
    UserSerializer, SwitchUserModeSerializer
)


class RegisterView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, created = Token.objects.get_or_create(user=user) 
            return Response({
                "message": "User registered successfully.",
                "token": token.key,
                "user": UserSerializer(user).data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            token, _ = Token.objects.get_or_create(user=user)
            return Response({
                "message": "Login successful.",
                "token": token.key,
                "user": UserSerializer(user).data
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# class RequestSaccoAdminAccess(APIView):
#     permission_classes = [IsAuthenticated]

#     def post(self, request):
#         user = request.user
#         if user.sacco_admin_requested:
#             return Response({"detail": "Request already submitted."}, status=status.HTTP_400_BAD_REQUEST)
#         user.sacco_admin_requested = True
#         user.save()
#         return Response({"detail": "Sacco Admin request sent."}, status=status.HTTP_200_OK)


class SwitchUserModeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SwitchUserModeSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            target = serializer.validated_data['switch_to']

            if target == 'passenger':
                user.is_passenger = True
                user.is_vehicle_owner = False
                user.is_sacco_admin = False

            elif target == 'vehicle_owner':
                user.is_passenger = False
                user.is_vehicle_owner = True
                user.is_sacco_admin = False

            elif target == 'sacco_admin':
                if not user.is_sacco_admin:
                    return Response({"detail": "Not approved as sacco admin."}, status=status.HTTP_403_FORBIDDEN)
                user.is_passenger = False
                user.is_vehicle_owner = False
                # is_sacco_admin already true

            user.save()
            return Response({
                "message": f"Switched to {target} mode.",
                "user": UserSerializer(user).data
            })

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


