import logging
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
from rest_framework.authtoken.models import Token
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
import requests
from django.contrib.auth import get_user_model
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.core.mail import send_mail
from django.shortcuts import redirect
from vehicles.email_service import SaccoEmailService
from django.urls import reverse
from django.contrib.auth import logout
try:
    from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
    from allauth.socialaccount.providers.oauth2.client import OAuth2Client
    from dj_rest_auth.registration.views import SocialLoginView
except ImportError:
    GoogleOAuth2Adapter = None
    OAuth2Client = None
    SocialLoginView = None

User = get_user_model()
logger = logging.getLogger(__name__)

class RegisterView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, created = Token.objects.get_or_create(user=user)
            
            # Send welcome email
            try:
                email_sent = SaccoEmailService.send_welcome_email(user)
                if email_sent:
                    logger.info(f"Welcome email sent successfully to {user.email}")
                else:
                    logger.warning(f"Failed to send welcome email to {user.email}")
            except Exception as e:
                # Log the error but don't fail the registration
                logger.error(f"Error sending welcome email to {user.email}: {str(e)}")
            
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
            
            # Check if user has permission for this role
            role_permissions = {
                'passenger': True,  # Everyone can be a passenger
                'vehicle_owner': user.is_vehicle_owner,
                'sacco_admin': user.is_sacco_admin
            }
            
            if not role_permissions.get(target_role, False):
                role_messages = {
                    'vehicle_owner': "You are not registered as a vehicle owner.",
                    'sacco_admin': "You are not approved as a sacco admin."
                }
                return Response({
                    "detail": role_messages.get(target_role, "You don't have access to this role.")
                }, status=status.HTTP_403_FORBIDDEN)
            
            # NEW LOGIC - Just update the current_role field
            user.current_role = target_role
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
                    # These should reflect the PERMISSIONS, not current role
                    "is_passenger": user.is_passenger,
                    "is_vehicle_owner": user.is_vehicle_owner,
                    "is_sacco_admin": user.is_sacco_admin,
                }
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserReviewsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        
        # Get current role - using the method from UserProfileSerializer
        def get_current_role(user):
            if user.is_sacco_admin:
                return 'sacco_admin'
            elif user.is_vehicle_owner:
                return 'vehicle_owner'
            else:
                return 'passenger'  # Default role
        
        current_role = get_current_role(user)
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


User = get_user_model()
logger = logging.getLogger(__name__)

@api_view(['POST'])
@permission_classes([AllowAny])
def google_auth(request):
    """
    Authenticate user with Google ID token OR access token and return Django Token
    Handles both mobile (ID token) and web (access token) authentication
    """
    id_token_str = request.data.get('id_token')
    access_token_str = request.data.get('access_token')
    
    if not id_token_str and not access_token_str:
        return Response(
            {'error': 'Either id_token or access_token is required'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        user_info = None
        auth_method = None
        
        # Try ID token first (for mobile)
        if id_token_str:
            try:
                user_info = verify_id_token(id_token_str)
                auth_method = 'id_token'
                logger.info("Successfully verified ID token")
            except Exception as e:
                logger.error(f"ID token verification failed: {str(e)}")
                # If ID token fails, try access token if available
                if not access_token_str:
                    raise e
        
        # Try access token (for web or fallback)
        if not user_info and access_token_str:
            try:
                user_info = verify_access_token(access_token_str)
                auth_method = 'access_token'
                logger.info("Successfully verified access token")
            except Exception as e:
                logger.error(f"Access token verification failed: {str(e)}")
                if not id_token_str:  # Only raise if we don't have ID token to fall back on
                    raise e
        
        if not user_info:
            return Response(
                {'error': 'Both token verifications failed'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Extract user information
        email = user_info['email']
        name = user_info.get('name', '')
        first_name = user_info.get('given_name', '')
        last_name = user_info.get('family_name', '')
        
        # Handle cases where given_name/family_name might not be available
        if not first_name and name:
            name_parts = name.split(' ')
            first_name = name_parts[0] if name_parts else ''
            last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''
        
        # Get or create user
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'username': email,
                'first_name': first_name,
                'last_name': last_name,
            }
        )
        
        # Update user info if not created and info has changed
        if not created:
            updated = False
            if user.first_name != first_name:
                user.first_name = first_name
                updated = True
            if user.last_name != last_name:
                user.last_name = last_name
                updated = True
            if updated:
                user.save()
        
        # Create or get Django Token (same as your existing login)
        token, created_token = Token.objects.get_or_create(user=user)
        
        return Response({
            'message': 'Google authentication successful',
            'token': token.key,
            'user': {
                'id': user.id,
                'email': user.email,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'name': f"{user.first_name} {user.last_name}".strip(),
                'current_role': getattr(user, 'current_role', 'passenger'),
                'is_passenger': getattr(user, 'is_passenger', True),
                'is_vehicle_owner': getattr(user, 'is_vehicle_owner', False),
                'is_sacco_admin': getattr(user, 'is_sacco_admin', False),
            },
            'created': created,
            'auth_method': auth_method
        })
        
    except Exception as e:
        logger.error(f"Google auth error: {str(e)}")
        return Response(
            {'error': f'Authentication failed: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
def verify_id_token(id_token_str):
    """
    Verify Google ID token and return user info
    """
    try:
        # Verify the token
        idinfo = id_token.verify_oauth2_token(
            id_token_str, 
            google_requests.Request(), 
            settings.GOOGLE_OAUTH2_CLIENT_ID
        )
        
        # Verify the issuer
        if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            raise ValueError('Wrong issuer.')
        
        return {
            'email': idinfo['email'],
            'name': idinfo.get('name', ''),
            'given_name': idinfo.get('given_name', ''),
            'family_name': idinfo.get('family_name', ''),
            'picture': idinfo.get('picture', ''),
            'sub': idinfo['sub']  # Google user ID
        }
        
    except ValueError as e:
        logger.error(f"ID token verification error: {str(e)}")
        raise Exception(f"Invalid ID token: {str(e)}")

def verify_access_token(access_token_str):
    """
    Verify Google access token and return user info
    """
    try:
        # Call Google's userinfo API
        response = requests.get(
            'https://www.googleapis.com/oauth2/v2/userinfo',
            headers={'Authorization': f'Bearer {access_token_str}'}
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to verify access token: {response.status_code}")
        
        user_info = response.json()
        
        # Validate that we got the required email field
        if 'email' not in user_info:
            raise Exception("No email in user info")
        
        return {
            'email': user_info['email'],
            'name': user_info.get('name', ''),
            'given_name': user_info.get('given_name', ''),
            'family_name': user_info.get('family_name', ''),
            'picture': user_info.get('picture', ''),
            'id': user_info.get('id', '')  # Google user ID
        }
        
    except Exception as e:
        logger.error(f"Access token verification error: {str(e)}")
        raise Exception(f"Failed to verify access token: {str(e)}")


@api_view(['POST'])
@permission_classes([AllowAny])
def request_password_reset(request):
    """
    Request password reset email
    """
    try:
        email = request.data.get('email')
        if not email:
            return Response(
                {'error': 'Email is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # For security, don't reveal if email exists or not
            return Response(
                {'message': 'If this email exists in our system, you will receive a password reset link shortly.'}, 
                status=status.HTTP_200_OK
            )
        
        # Generate reset token
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        
        
        # Send email
        subject = 'PSV Finder - Password Reset Request'
        message = f"""
        Hello {user.username},
        
        You requested a password reset for your PSV Finder account.
        
        Reset Token: {token}
        User ID: {uid}
        
        If you didn't request this reset, please ignore this email.
        
        Best regards,
        PSV Finder Team
        """
        
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
            
            return Response(
                {'message': 'Password reset email sent successfully'}, 
                status=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Failed to send password reset email: {str(e)}")
            return Response(
                {'error': 'Failed to send email. Please try again later.'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
    except Exception as e:
        logger.error(f"Password reset request error: {str(e)}")
        return Response(
            {'error': 'An error occurred. Please try again later.'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@permission_classes([AllowAny])
def validate_reset_token(request):
    """
    Validate password reset token
    """
    try:
        token = request.data.get('token')
        uid = request.data.get('uid')
        
        if not token or not uid:
            return Response(
                {'error': 'Token and uid are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=user_id)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response(
                {'error': 'Invalid token'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate token
        if not default_token_generator.check_token(user, token):
            return Response(
                {'error': 'Invalid or expired token'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response(
            {'message': 'Token is valid', 'user_id': user.id}, 
            status=status.HTTP_200_OK
        )
    
    except Exception as e:
        logger.error(f"Token validation error: {str(e)}")
        return Response(
            {'error': 'An error occurred. Please try again later.'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password(request):
    """
    Reset password with token
    """
    try:
        token = request.data.get('token')
        uid = request.data.get('uid')
        new_password = request.data.get('new_password')
        
        if not token or not uid or not new_password:
            return Response(
                {'error': 'Token, uid, and new_password are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=user_id)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response(
                {'error': 'Invalid token'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate token
        if not default_token_generator.check_token(user, token):
            return Response(
                {'error': 'Invalid or expired token'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Reset password
        user.set_password(new_password)
        user.save()
        
        return Response(
            {'message': 'Password reset successfully'}, 
            status=status.HTTP_200_OK
        )
    
    except Exception as e:
        logger.error(f"Password reset error: {str(e)}")
        return Response(
            {'error': 'An error occurred. Please try again later.'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

# Google OAuth Views (using django-allauth)
if SocialLoginView and GoogleOAuth2Adapter and OAuth2Client:
    class GoogleLoginView(SocialLoginView):
        """
        Google OAuth2 Login View for Flutter
        POST /auth/google/login/
        
        Expected request body:
        {
            "access_token": "google_access_token_from_flutter"
        }
        """
        adapter_class = GoogleOAuth2Adapter
        client_class = OAuth2Client

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def google_logout_view(request):
    """
    Google OAuth2 Logout View for Flutter
    """
    try:
        # Delete the user's token
        if hasattr(request.user, 'auth_token'):
            request.user.auth_token.delete()
        
        # Logout the user
        logout(request)
        return Response({
            'message': 'Successfully logged out',
            'success': True
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            'error': 'Logout failed',
            'message': str(e),
            'success': False
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def google_login_redirect(request):
    """
    Redirect to Google OAuth2 login
    """
    google_login_url = reverse('google_oauth2_login')
    return redirect(google_login_url)

@api_view(['GET'])
def auth_status(request):
    """
    Check authentication status for Flutter
    """
    if request.user.is_authenticated:
        return Response({
            'authenticated': True,
            'user': {
                'id': request.user.id,
                'email': request.user.email,
                'username': request.user.username,
                'first_name': getattr(request.user, 'first_name', ''),
                'last_name': getattr(request.user, 'last_name', ''),
            }
        })
    else:
        return Response({
            'authenticated': False,
            'user': None
        })