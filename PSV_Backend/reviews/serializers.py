from rest_framework import serializers
from .models import PassengerReview, OwnerReview


class PassengerReviewSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()  
    sacco = serializers.StringRelatedField() 
    average = serializers.FloatField() 
    class Meta:
        model = PassengerReview
        fields = "__all__"
        read_only_fields = ['user', 'average', 'created_at']

class OwnerReviewSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()  
    sacco = serializers.StringRelatedField() 
    average = serializers.FloatField() 
    class Meta:
        model = OwnerReview
        fields =[
            'user', 'sacco', 'payment_punctuality', 'driver_responsibility',
            'rate_fairness', 'support', 'transparency', 'overall', 
            'average', 'comment', 'created_at'
        ]
        read_only_fields = ['user', 'average', 'created_at']