from rest_framework import serializers
from sacco.models import Sacco, SaccoAdminRequest
from routes.serializers import RouteSerializer


class SaccoSerializer(serializers.ModelSerializer):
    sacco_admin = serializers.StringRelatedField()
    routes = RouteSerializer(many=True, read_only=True)
    commission_structure = serializers.SerializerMethodField()
    
    class Meta:
        model = Sacco
        fields = '__all__'  # or list specific fields including new ones
    
    def get_commission_structure(self, obj):
        return {
            'rate': obj.commission_rate,
            'daily_target': obj.daily_target,
            'weekly_bonus_threshold': obj.weekly_bonus_threshold,
            'weekly_bonus_amount': obj.weekly_bonus_amount,
        }

# serializers.py
class SaccoPOVSerializer(serializers.ModelSerializer):
    sacco_admin = serializers.StringRelatedField()  # Assuming user is a ForeignKey to User model
    class Meta:
        model= Sacco
        fields = [
            "id", "name", "location", "date_established",
            "registration_number", "contact_number", "email","sacco_admin"]

  

class SaccoAdminRequestSerializer(serializers.ModelSerializer):
    sacco = SaccoSerializer(read_only=True)  # Return full Sacco details
    sacco_id = serializers.PrimaryKeyRelatedField(
        queryset=Sacco.objects.all(), source="sacco", write_only=True, required=False
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
    
    def validate(self, data):
        # Check if sacco_id was provided in the request (before it gets processed to 'sacco')
        sacco_id_provided = 'sacco_id' in self.initial_data and self.initial_data['sacco_id']
        
        if not sacco_id_provided:  # No existing sacco selected, validate new sacco fields
            required_fields = [
                "sacco_name", "location", "date_established",
                "registration_number", "contact_number", "email"
            ]
            missing_fields = [field for field in required_fields if not self.initial_data.get(field)]
            if missing_fields:
                raise serializers.ValidationError(
                    f"You must provide all required Sacco details if no existing Sacco is selected: {', '.join(missing_fields)}"
                )
        return data