from django.urls import path
from .views import (
    RegisterView, LoginView,
    SwitchUserModeView, UserListView
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('switch-user-mode/', SwitchUserModeView.as_view(), name='switch_user_mode'),
    # path('request-admin/', RequestSaccoAdminAccess.as_view(), name='request_admin'),
    path('user-list/', UserListView.as_view(), name='user_list'),
]
