from rest_framework import serializers
from .models import User
from django.contrib.auth import authenticate

from django.contrib.auth import get_user_model
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(username=data['username'], password=data['password'])
        if user is None:
            raise serializers.ValidationError("Invalid credentials.")
        return {'user': user}


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email', 'is_passenger', 'is_vehicle_owner', 'is_sacco_admin']


User = get_user_model()

class SwitchUserModeSerializer(serializers.Serializer):
    switch_to = serializers.ChoiceField(
        choices=['passenger', 'vehicle_owner', 'sacco_admin'],
        required=True
    )
    
    def validate_switch_to(self, value):
        """Validate the switch_to value"""
        valid_roles = ['passenger', 'vehicle_owner', 'sacco_admin']
        if value not in valid_roles:
            raise serializers.ValidationError("Invalid role specified.")
        return value

class UserProfileSerializer(serializers.ModelSerializer):
    current_role = serializers.SerializerMethodField()
    available_roles = serializers.SerializerMethodField()
    reviews_count = serializers.SerializerMethodField()
    can_switch_roles = serializers.SerializerMethodField()

    class Meta:
        model = get_user_model()
        fields = [
            'id', 'username', 'email', 'phone_number', 'first_name', 'last_name',
            'current_role', 'available_roles',
            'is_passenger', 'is_vehicle_owner', 'is_sacco_admin',
            'date_joined', 'is_active',
            'reviews_count', 'can_switch_roles'
        ]

    def get_current_role(self, obj):
        # Return the currently active role based on the flags
        if obj.is_sacco_admin:
            return 'sacco_admin'
        elif obj.is_vehicle_owner:
            return 'vehicle_owner'
        else:
            return 'passenger'  # Default role

    def get_available_roles(self, obj):
        """
        Get all roles the user can switch to (excluding their current role)
        """
        available_roles = []
        current_role = self.get_current_role(obj)
        
        # Everyone can be a passenger (unless they're already a passenger)
        if current_role != 'passenger':
            available_roles.append('passenger')
        
        # If user has vehicle_owner flag but isn't currently in that role
        if obj.is_vehicle_owner and current_role != 'vehicle_owner':
            available_roles.append('vehicle_owner')
        
        # If user has sacco_admin flag but isn't currently in that role
        if obj.is_sacco_admin and current_role != 'sacco_admin':
            available_roles.append('sacco_admin')
        
        return available_roles

    def get_can_switch_roles(self, obj):
        """
        Determine if user can switch roles (has more than one role available)
        """
        available_roles = self.get_available_roles(obj)
        return len(available_roles) > 0

    def get_reviews_count(self, obj):
        # This should match your Review model structure
        try:
            if hasattr(obj, 'reviews'):
                return obj.reviews.count()
            else:
                # Fallback if you have separate review models
                from django.db import models
                review_count = 0
                if hasattr(obj, 'passenger_reviews'):
                    review_count += obj.passenger_reviews.count()
                if hasattr(obj, 'owner_reviews'):
                    review_count += obj.owner_reviews.count()
                return review_count
        except:
            return 0


class UpdateProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email', 'phone_number']

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField()
    new_password = serializers.CharField()
