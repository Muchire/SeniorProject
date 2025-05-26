from django.urls import path
from sacco.views import SaccoListCreateView, SaccoDetailView

urlpatterns = [
    path('', SaccoListCreateView.as_view(), name='sacco-list-create'),
    path('<int:pk>/', SaccoDetailView.as_view(), name='sacco-detail'),
]
