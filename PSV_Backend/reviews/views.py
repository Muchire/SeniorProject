from rest_framework import generics, permissions
from rest_framework.generics import ListCreateAPIView
from .models import PassengerReview, OwnerReview
from .serializers import PassengerReviewSerializer, OwnerReviewSerializer

class PassengerReviewListCreateView(generics.ListCreateAPIView):
    queryset = PassengerReview.objects.all()
    serializer_class = PassengerReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class PassengerReviewsBySaccoView(ListCreateAPIView):
    serializer_class = PassengerReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]  # Added this line

    def get_queryset(self):
        sacco_id = self.kwargs.get('sacco_id')
        return PassengerReview.objects.filter(sacco_id=sacco_id)
    
    def perform_create(self, serializer):
        # Get the sacco_id from the URL and set both user and sacco
        sacco_id = self.kwargs.get('sacco_id')
        serializer.save(user=self.request.user, sacco_id=sacco_id)

class OwnerReviewListCreateView(generics.ListCreateAPIView):
    queryset = OwnerReview.objects.all()
    serializer_class = OwnerReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class OwnerReviewsBySaccoView(ListCreateAPIView):  # Fixed typo: "OwnmerReviewsBySaccoView" -> "OwnerReviewsBySaccoView"
    serializer_class = OwnerReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]  # Added this line

    def get_queryset(self):
        sacco_id = self.kwargs.get('sacco_id')
        return OwnerReview.objects.filter(sacco_id=sacco_id)
    
    def perform_create(self, serializer):
        # Added this method for consistency
        sacco_id = self.kwargs.get('sacco_id')
        serializer.save(user=self.request.user, sacco_id=sacco_id)

class PassengerReviewDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = PassengerReview.objects.all()
    serializer_class = PassengerReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

class OwnerReviewDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = OwnerReview.objects.all()
    serializer_class = OwnerReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]