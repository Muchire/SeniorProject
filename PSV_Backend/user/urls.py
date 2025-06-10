from django.urls import path
from .views import (
    RegisterView, LoginView,
    SwitchUserModeView, UserListView,UserProfileView, UserReviewsView,UpdateProfileView,ChangePasswordView, DeactivateUserView
)

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
    path('passenger-dashboard/', lambda request: Response({'message': 'Passenger Dashboard'}), name='passenger_dashboard'),
    path('vehicle-owner-dashboard/', lambda request: Response({'message': 'Vehicle Owner Dashboard'}), name='vehicle_owner_dashboard'),
    path('admin-dashboard/', lambda request: Response({'message': 'Admin Dashboard'}), name='admin_dashboard'),
]
