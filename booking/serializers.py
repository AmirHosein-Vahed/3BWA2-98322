from rest_framework import serializers
from .models import Table, Reservation

class ReservationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reservation
        fields = '__all__'
        read_only_fields = ['id', 'cost', 'booking_time', 'is_cancelled']

class BookingSerializer(serializers.ModelSerializer):
    number_of_individuals = serializers.IntegerField(min_value=1)

    class Meta:
        model = Table
        fields = '__all__'
        read_only_fields = ['id']