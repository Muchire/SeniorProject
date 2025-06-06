from django.urls import path
from .views import (
    PassengerReviewListCreateView,
    OwnerReviewListCreateView,
    PassengerReviewDetailView,
    OwnerReviewDetailView,
)

urlpatterns = [
    path('passenger-reviews/', PassengerReviewListCreateView.as_view(), name='passenger-review-list-create'),
    path('owner-reviews/', OwnerReviewListCreateView.as_view(), name='owner-review-list-create'),
    path('passenger-reviews/<int:pk>/', PassengerReviewDetailView.as_view(), name='passenger-review-detail'),
    path('owner-reviews/<int:pk>/', OwnerReviewDetailView.as_view(), name='owner-review-detail'),
]
