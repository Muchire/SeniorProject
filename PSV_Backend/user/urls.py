from django.urls import path
from django.http import JsonResponse
from django.shortcuts import redirect
from .views import (
    RegisterView, LoginView,
    SwitchUserModeView, UserListView,UserProfileView, UserReviewsView,UpdateProfileView,ChangePasswordView, DeactivateUserView
)


def passenger_dashboard(request):
    return JsonResponse({'message': 'Passenger Dashboard'})

def vehicle_owner_dashboard(request):
    return JsonResponse({'message': 'Vehicle Owner Dashboard'})

def admin_dashboard(request):
    # Option 1: Return JSON response
    return JsonResponse({'message': 'Admin Dashboard'})
    
urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('switch-user-mode/', SwitchUserModeView.as_view(), name='switch_user_mode'),
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    path('profile/update/', UpdateProfileView.as_view(), name='update-profile'),
    path('password/change/', ChangePasswordView.as_view(), name='change-password'),
    path('profile/deactivate/', DeactivateUserView.as_view(), name='deactivate-user'),
    path('my-reviews/', UserReviewsView.as_view(), name='my-reviews'),
    path('user-list/', UserListView.as_view(), name='user_list'),
    
    # Role-specific dashboard redirects
    path('passenger-dashboard/', passenger_dashboard, name='passenger_dashboard'),
    path('vehicle-owner-dashboard/', vehicle_owner_dashboard, name='vehicle_owner_dashboard'),
    path('admin-dashboard/', admin_dashboard, name='admin_dashboard'),
]
