from django.db import models
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Event, Donation


# ============================
# USER SERIALIZER (same)
# ============================
class UserSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'is_staff', 'is_superuser', 'role']

    def get_role(self, obj):
        if obj.is_superuser:
            return 'Admin'
        elif obj.is_staff:
            return 'HR'
        else:
            return 'Employee'


# ============================
# EVENT SERIALIZER (same)
# ============================
class EventSerializer(serializers.ModelSerializer):
    total_donations = serializers.SerializerMethodField()
    image = serializers.ImageField(use_url=True)

    class Meta:
        model = Event
        fields = [
            "id",
            "title",
            "description",
            "date",
            "location",
            "image",
            "total_donations",
        ]

    def get_total_donations(self, obj):
        total = obj.donations.aggregate(total=models.Sum("amount"))["total"]
        return total or 0


# ============================
# DONATION SERIALIZER
# ============================
class DonationSerializer(serializers.ModelSerializer):
    donor = serializers.ReadOnlyField(source='donor.username')
    donor_email = serializers.ReadOnlyField(source='donor.email')
    event_title = serializers.ReadOnlyField(source='event.title')

    class Meta:
        model = Donation
        fields = ['id', 'event_title', 'donor', 'donor_email', 'amount', 'date']
        read_only_fields = ['donor', 'date', 'event_title']

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero.")
        return value

    def create(self, validated_data):
        request = self.context.get('request')
        event = self.context.get('event')

        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError("Authentication required.")

        if not event:
            raise serializers.ValidationError("Invalid event.")

        return Donation.objects.create(
            donor=request.user,
            event=event,
            amount=validated_data['amount']
        )
