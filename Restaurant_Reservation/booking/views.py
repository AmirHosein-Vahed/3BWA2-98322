from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from .models import Table, Reservation, MIN_SEATS_PER_TABLE, MAX_SEATS_PER_TABLE, SEAT_COST, TOTAL_TABLES
from .serializers import ReservationSerializer, BookingSerializer


class BookView(APIView):
    """
    API view for creating a new reservation.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = BookingSerializer(data=request.data)
        if serializer.is_valid():
            number_of_individuals = serializer.validated_data['number_of_individuals']
            user = request.user

            # Apply the rule for odd number of seats
            seats_to_book = number_of_individuals
            if seats_to_book % 2 != 0 and seats_to_book not in range(MIN_SEATS_PER_TABLE, MAX_SEATS_PER_TABLE + 1):
                 seats_to_book += 1 # Assign an even number of seats

            # Find an available table with enough seats
            # Prioritize tables that match the exact number of seats or are slightly larger
            available_tables = Table.objects.filter(
                is_available=True,
                seats__gte=seats_to_book
            ).order_by('seats') # Order by seats to find the cheapest option first

            if not available_tables.exists():
                return Response({"error": "No available tables for the requested number of seats."},
                                status=status.HTTP_400_BAD_REQUEST)

            # Select the first available table (cheapest option based on seat count)
            chosen_table = available_tables.first()

            # Calculate the cost
            if seats_to_book == chosen_table.seats:
                # Booking the entire table
                cost = (chosen_table.seats - 1) * SEAT_COST
            else:
                # Booking individual seats
                cost = seats_to_book * SEAT_COST

            # Create the reservation
            reservation = Reservation.objects.create(
                user=user,
                table=chosen_table,
                seats_booked=seats_to_book,
                cost=cost
            )

            # Mark the table as unavailable
            chosen_table.is_available = False
            chosen_table.save()

            serializer = ReservationSerializer(reservation)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CancelView(APIView):
    """
    API view for cancelling a reservation.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, reservation_id):
        try:
            reservation = Reservation.objects.get(id=reservation_id, user=request.user, is_cancelled=False)
        except Reservation.DoesNotExist:
            return Response({"error": "Reservation not found or already cancelled."},
                            status=status.HTTP_404_NOT_FOUND)

        # Mark the reservation as cancelled
        reservation.is_cancelled = True
        reservation.save()

        # Make the table available again
        table = reservation.table
        table.is_available = True
        table.save()

        return Response({"message": "Reservation cancelled successfully."}, status=status.HTTP_200_OK)