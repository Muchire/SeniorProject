from django.urls import path
from sacco.views import SaccoListCreateView, SaccoDetailView, RequestSaccoAdminView, ApproveSaccoAdminView, SaccoAdminRequestListView

urlpatterns = [
    path('', SaccoListCreateView.as_view(), name='sacco-list-create'),
    path('<int:pk>/', SaccoDetailView.as_view(), name='sacco-detail'),
    #request to be an admin
    path('request-admin/', RequestSaccoAdminView.as_view(), name='request_sacco_admin'),
    #approve admin request
    path('approve-admin/<int:pk>/', ApproveSaccoAdminView.as_view(), name='approve_sacco_admin'),
    #list of admin requests
    path('admin-requests/', SaccoAdminRequestListView.as_view(), name='sacco_admin_requests'),

]
