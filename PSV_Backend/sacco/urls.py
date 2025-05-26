from django.urls import path
from sacco.views import SaccoListCreateView, SaccoDetailView, RequestSaccoAdminView, ApproveSaccoAdminView

urlpatterns = [
    path('', SaccoListCreateView.as_view(), name='sacco-list-create'),
    path('<int:pk>/', SaccoDetailView.as_view(), name='sacco-detail'),
    path('request-admin/', RequestSaccoAdminView.as_view(), name='request_sacco_admin'),
    path('approve-admin/<int:pk>/', ApproveSaccoAdminView.as_view(), name='approve_sacco_admin'),

]
