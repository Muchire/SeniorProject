from rest_framework import serializers
from sacco.models import Sacco, SaccoAdminRequest


class SaccoSerializer(serializers.ModelSerializer):
    class Meta:
        model= Sacco
        fields = '__all__'
class SaccoAdminRequestSerializer(serializers.ModelSerializer):
    username = serializers.SerializerMethodField()          
    class Meta:
        model = SaccoAdminRequest
        fields = [ 'id','username','sacco_name', 'is_approved']
    read_only_fields = ['is_approved', 'created_at']    

# ''' this ensures I get the username of the user tha has requested  to be a sacco admin'''
    def get_username(self, obj):
        return obj.user.username if obj.user else None                                                                                                                             