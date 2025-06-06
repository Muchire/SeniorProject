from rest_framework import generics, permissions
from .models import PassengerReview, OwnerReview
from .serializers import PassengerReviewSerializer, OwnerReviewSerializer

class PassengerReviewListCreateView(generics.ListCreateAPIView):
    queryset = PassengerReview.objects.all()
    serializer_class = PassengerReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class OwnerReviewListCreateView(generics.ListCreateAPIView):
    queryset = OwnerReview.objects.all()
    serializer_class = OwnerReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class PassengerReviewDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = PassengerReview.objects.all()
    serializer_class = PassengerReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class OwnerReviewDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = OwnerReview.objects.all()
    serializer_class = OwnerReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
