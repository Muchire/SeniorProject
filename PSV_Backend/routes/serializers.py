from rest_framework import serializers
from .models import Route, RouteStop

class RouteStopSerializer(serializers.ModelSerializer):
    class Meta:
        model = RouteStop
        fields = ['stage_name', 'order']

class RouteSerializer(serializers.ModelSerializer):
    sacco_name = serializers.CharField(source='sacco.name', read_only=True)
    stops = RouteStopSerializer(many=True, read_only=True)

    class Meta:
        model = Route
        fields = [
            'id', 'start_location', 'end_location', 'distance',
            'duration', 'fare', 'sacco', 'sacco_name', 'stops'
        ]
        read_only_fields = ['sacco_name', 'stops']