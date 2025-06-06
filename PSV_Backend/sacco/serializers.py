from rest_framework import serializers
from sacco.models import Sacco, SaccoAdminRequest


class SaccoSerializer(serializers.ModelSerializer):
    class Meta:
        model= Sacco
        fields = '__all__'
# serializers.py

class SaccoAdminRequestSerializer(serializers.ModelSerializer):
    sacco = serializers.PrimaryKeyRelatedField(
        queryset=Sacco.objects.all(), required=False, allow_null=True
    )

    class Meta:
        model = SaccoAdminRequest
        fields = '__all__'
        read_only_fields = ['is_approved', 'reviewed', 'user']

    def validate(self, data):
        # If no sacco is selected, user must provide full sacco details
        if not data.get("sacco"):
            required_fields = ['sacco_name', 'location', 'registration_number', 'contact_number', 'email']
            missing = [field for field in required_fields if not self.initial_data.get(field)]
            if missing:
                raise serializers.ValidationError({
                    "missing_fields": f"Missing fields for new Sacco: {', '.join(missing)}"
                })
        return data

    def create(self, validated_data):
        user = self.context['request'].user

        # If no existing sacco is selected, create a new one
        if not validated_data.get("sacco"):
            sacco = Sacco.objects.create(
                name=validated_data['sacco_name'],
                location=validated_data['location'],
                date_established=validated_data.get('date_established'),
                registration_number=validated_data['registration_number'],
                contact_number=validated_data['contact_number'],
                email=validated_data['email'],
                website=validated_data.get('website'),
            )
            validated_data['sacco'] = sacco

        validated_data['user'] = user
        return super().create(validated_data)
