from rest_framework import serializers
from sacco.models import Sacco, SaccoAdminRequest


class SaccoSerializer(serializers.ModelSerializer):
    class Meta:
        model= Sacco
        fields = '__all__'
class SaccoAdminRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = SaccoAdminRequest
        fields = ['id', 'sacco_name', 'sacco_location', 'approved', 'created_at']
        read_only_fields = ['approved', 'created_at']                                                                                                                                 