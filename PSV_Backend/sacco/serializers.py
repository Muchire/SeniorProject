from rest_framework import serializers
from sacco.models import Sacco


class SaccoSerializer(serializers.ModelSerializer):
    class Meta:
        model= Sacco
        fields = '__all__'
                                                                                                                                     