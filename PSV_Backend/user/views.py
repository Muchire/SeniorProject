from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.models import Token
from django.contrib.auth import get_user_model
from reviews.models import PassengerReview
from reviews.models import OwnerReview
from .models import User
from .serializers import (
    RegisterSerializer, LoginSerializer,
    UserSerializer, SwitchUserModeSerializer,ChangePasswordSerializer,UpdateProfileSerializer,UserProfileSerializer
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
class UserListView(APIView):
    permission_classes = [IsAuthenticated]
    queryset = User.objects.all()

    def get(self, request):
        queryset = User.objects.all()
        serializer = UserSerializer(queryset, many=True)
        return Response(serializer.data)


User = get_user_model()

class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        
        # Use the serializer for consistency
        serializer = UserProfileSerializer(user)
        profile_data = serializer.data
        
        # Add any additional computed fields if needed
        profile_data['date_joined'] = user.date_joined.strftime('%Y-%m-%d')
        
        return Response(profile_data, status=status.HTTP_200_OK)

class SwitchUserModeView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Switch user's active role"""
        serializer = SwitchUserModeSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            target_role = serializer.validated_data['switch_to']
            
            # Get available roles using the same logic as the profile serializer
            profile_serializer = UserProfileSerializer(user)
            current_role = profile_serializer.get_current_role(user)
            available_roles = profile_serializer.get_available_roles(user)
            
            # Check if the target role is available
            all_eligible_roles = available_roles + [current_role]
            
            if target_role not in all_eligible_roles:
                role_messages = {
                    'passenger': "You don't have passenger access.",
                    'vehicle_owner': "You are not registered as a vehicle owner.",
                    'sacco_admin': "You are not approved as a sacco admin."
                }
                return Response({
                    "detail": role_messages.get(target_role, "You don't have access to this role.")
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Reset all role flags
            user.is_passenger = False
            user.is_vehicle_owner = False
            user.is_sacco_admin = False
            
            # Set the target role as active
            if target_role == 'passenger':
                user.is_passenger = True
            elif target_role == 'vehicle_owner':
                user.is_vehicle_owner = True
            elif target_role == 'sacco_admin':
                user.is_sacco_admin = True
            
            user.save()
            
            # Determine redirect URL based on role
            redirect_urls = {
                'passenger': '/',
                'vehicle_owner': '/vehicle-owner-dashboard/',
                'sacco_admin': '/admin-dashboard/'
            }
            
            return Response({
                "message": f"Successfully switched to {target_role} mode.",
                "current_role": target_role,
                "redirect_url": redirect_urls.get(target_role, '/'),
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "current_role": target_role,
                    "is_passenger": user.is_passenger,
                    "is_vehicle_owner": user.is_vehicle_owner,
                    "is_sacco_admin": user.is_sacco_admin,
                }
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# class UserStatsView(APIView):
#     permission_classes = [IsAuthenticated]
    
#     def get(self, request):
#         """Get user statistics"""
#         user = request.user
        
#         # Get reviews count
#         reviews_count = Review.objects.filter(passenger=user).count()
        
#         # Mock data for trips and favorites (implement based on your models)
#         # trips_count = Trip.objects.filter(passenger=user).count()
#         # favorites_count = Favorite.objects.filter(user=user).count()
        
#         stats = {
#             'reviews_count': reviews_count,
#             'trips_count': 0,  # Replace with actual count
#             'favorites_count': 0,  # Replace with actual count
#         }
        
#         return Response(stats, status=status.HTTP_200_OK)

class UserReviewsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        current_role = 'passenger'
        if user.is_vehicle_owner:
            current_role = 'vehicle_owner'
        elif user.is_sacco_admin:
            current_role = 'sacco_admin'

        reviews_data = []

        if current_role == 'passenger':
            reviews = PassengerReview.objects.filter(user=user).order_by('-created_at')
            limit = request.query_params.get('limit')
            if limit:
                try:
                    reviews = reviews[:int(limit)]
                except ValueError:
                    pass

            for review in reviews:
                reviews_data.append({
                    'id': review.id,
                    'role': 'passenger',
                    'sacco_name': review.sacco.name,
                    'overall': review.overall,
                    'cleanliness': review.cleanliness,
                    'punctuality': review.punctuality,
                    'comfort': review.comfort,
                    'comment': review.comment,
                    'created_at': review.created_at.strftime('%Y-%m-%d %H:%M'),
                    'average': float(review.average),
                })

        elif current_role == 'vehicle_owner':
            reviews = OwnerReview.objects.filter(user=user).order_by('-created_at')
            limit = request.query_params.get('limit')
            if limit:
                try:
                    reviews = reviews[:int(limit)]
                except ValueError:
                    pass

            for review in reviews:
                reviews_data.append({
                    'id': review.id,
                    'role': 'vehicle_owner',
                    'sacco_name': review.sacco.name,
                    'overall': review.overall,
                    'payment_punctuality': review.payment_punctuality,
                    'driver_responsibility': review.driver_responsibility,
                    'rate_fairness': review.rate_fairness,
                    'support': review.support,
                    'transparency': review.transparency,
                    'comment': review.comment,
                    'created_at': review.created_at.strftime('%Y-%m-%d %H:%M'),
                    'average': float(review.average),
                })

        # For sacco_admin, we don't return reviews (admins don't post reviews)
        return Response(reviews_data, status=status.HTTP_200_OK)
class UpdateProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        serializer = UpdateProfileSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Profile updated successfully."})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            # Fix: Use check_password method correctly
            if not user.check_password(serializer.validated_data['old_password']):
                return Response({"error": "Incorrect old password."}, status=status.HTTP_400_BAD_REQUEST)

            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response({"message": "Password changed successfully."})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DeactivateUserView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        user = request.user
        user.is_active = False
        user.save()
        return Response({"message": "User account deactivated."}, status=status.HTTP_200_OK)
