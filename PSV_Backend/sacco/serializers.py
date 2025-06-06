from rest_framework import serializers
from sacco.models import Sacco, SaccoAdminRequest


class SaccoSerializer(serializers.ModelSerializer):
    sacco_admin = serializers.StringRelatedField()  # Assuming user is a ForeignKey to User model
    class Meta:
        model= Sacco
        fields = '__all__'

    
# serializers.py

class SaccoAdminRequestSerializer(serializers.ModelSerializer):
    sacco = SaccoSerializer(read_only=True)  # Return full Sacco details
    sacco_id = serializers.PrimaryKeyRelatedField(
        queryset=Sacco.objects.all(), source="sacco", write_only=True
    )
    user = serializers.StringRelatedField()
    class Meta:
        model = SaccoAdminRequest
        
        fields = [
            "id", "sacco", "sacco_id", "sacco_name", "location",
            "date_established", "registration_number", "contact_number",
            "email", "website", "is_approved", "reviewed", "user"
        ]
        read_only_fields = ["is_approved", "reviewed", "user"]
        

    def to_representation(self, instance):
        """Ensure Sacco details are returned even if requested for an existing Sacco"""
        representation = super().to_representation(instance)

        if instance.sacco:  # If sacco exists, auto-fill fields
            representation["sacco_name"] = instance.sacco.name
            representation["location"] = instance.sacco.location
            representation["date_established"] = instance.sacco.date_established
            representation["registration_number"] = instance.sacco.registration_number
            representation["contact_number"] = instance.sacco.contact_number
            representation["email"] = instance.sacco.email
            representation["website"] = instance.sacco.website

        return representation
