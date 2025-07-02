from django.urls import include, path
from django.http import JsonResponse
from django.shortcuts import redirect
from .views import (
    RegisterView, LoginView,
    SwitchUserModeView, UserListView, UserProfileView, UserReviewsView,
    UpdateProfileView, ChangePasswordView, DeactivateUserView, google_auth,
    request_password_reset, validate_reset_token, reset_password,
    GoogleLoginView, google_login_redirect, google_logout_view, auth_status,
    send_password_reset_otp, verify_password_reset_otp, reset_password_with_otp
)


def passenger_dashboard(request):
    return JsonResponse({'message': 'Passenger Dashboard'})

def vehicle_owner_dashboard(request):
    return JsonResponse({'message': 'Vehicle Owner Dashboard'})

def admin_dashboard(request):
    return JsonResponse({'message': 'Admin Dashboard'})
    
urlpatterns = [
    # Google Authentication
    path('google-auth/', google_auth, name='google_auth'),
    path('google/login/', GoogleLoginView.as_view(), name='google_login'),
    path('google/logout/', google_logout_view, name='google_logout'),
    path('google/login/redirect/', google_login_redirect, name='google_login_redirect'),
    
    # Password Reset
    path('auth/request-password-reset/', request_password_reset, name='request_password_reset'),
    path('auth/validate-reset-token/', validate_reset_token, name='validate_reset_token'),
    path('auth/reset-password/', reset_password, name='reset_password'),
    
    # Django Allauth Google OAuth
    path('auth/google/login/', include('allauth.socialaccount.urls')),
    path('auth/password-reset/send-otp/', send_password_reset_otp, name='send_password_reset_otp'),
    path('auth/password-reset/verify-otp/', verify_password_reset_otp, name='verify_password_reset_otp'),
    path('auth/password-reset/confirm/', reset_password_with_otp, name='reset_password_with_otp'),
        
    # Basic Authentication
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('auth/status/', auth_status, name='auth_status'),
    
    # User Management
    path('switch-user-mode/', SwitchUserModeView.as_view(), name='switch_user_mode'),
    path('profile/', UserProfileView.as_view(), name='user_profile'),
    path('profile/update/', UpdateProfileView.as_view(), name='update_profile'),
    path('password/change/', ChangePasswordView.as_view(), name='change_password'),
    path('profile/deactivate/', DeactivateUserView.as_view(), name='deactivate_user'),
    path('my-reviews/', UserReviewsView.as_view(), name='my_reviews'),
    path('user-list/', UserListView.as_view(), name='user_list'),
    
    # Role-specific dashboard redirects
    path('passenger-dashboard/', passenger_dashboard, name='passenger_dashboard'),
    path('vehicle-owner-dashboard/', vehicle_owner_dashboard, name='vehicle_owner_dashboard'),
    path('admin-dashboard/', admin_dashboard, name='admin_dashboard'),
]