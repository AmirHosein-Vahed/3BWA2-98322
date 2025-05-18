from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User

from .models import Table, Reservation, SEAT_COST

class BookingAPITests(APITestCase):
    """
    Tests for the booking and cancellation APIs.
    """

    def setUp(self):
        """
        Set up test data: create a user and some tables.
        """
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.client.login(username='testuser', password='testpassword')

        # Create tables with varying seat counts
        Table.objects.create(table_number=1, seats=4, is_available=True)
        Table.objects.create(table_number=2, seats=6, is_available=True)
        Table.objects.create(table_number=3, seats=10, is_available=True)
        Table.objects.create(table_number=4, seats=4, is_available=False) # Unavailable table

    def test_successful_booking(self):
        """
        Test booking a table successfully.
        """
        url = reverse('book')
        data = {'number_of_individuals': 5} # Should book 6 seats
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Reservation.objects.count(), 1)
        reservation = Reservation.objects.first()
        self.assertEqual(reservation.user, self.user)
        self.assertEqual(reservation.seats_booked, 6)
        self.assertEqual(reservation.cost, 6 * SEAT_COST) # Cost for 6 seats
        self.assertFalse(reservation.table.is_available) # Table should be marked as unavailable

    def test_booking_odd_number_not_matching_table_size(self):
        """
        Test booking an odd number of seats that doesn't match a table size.
        Should book the next even number.
        """
        url = reverse('book')
        data = {'number_of_individuals': 3} # Should book 4 seats
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Reservation.objects.count(), 1)
        reservation = Reservation.objects.first()
        self.assertEqual(reservation.seats_booked, 4)
        self.assertEqual(reservation.cost, 4 * SEAT_COST)

    def test_booking_odd_number_matching_table_size(self):
        """
        Test booking an odd number of seats that matches a table size.
        Should book that exact number.
        """
        # Create a table with an odd number of seats within the allowed range
        Table.objects.create(table_number=5, seats=7, is_available=True)

        url = reverse('book')
        data = {'number_of_individuals': 7} # Should book 7 seats
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Reservation.objects.count(), 1)
        reservation = Reservation.objects.first()
        self.assertEqual(reservation.seats_booked, 7)
        self.assertEqual(reservation.cost, (7 - 1) * SEAT_COST) # Cost for entire table

    def test_booking_no_available_tables(self):
        """
        Test booking when no tables are available for the requested number of seats.
        """
        # Make all tables unavailable
        Table.objects.update(is_available=False)

        url = reverse('book')
        data = {'number_of_individuals': 5}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'No available tables for the requested number of seats.')
        self.assertEqual(Reservation.objects.count(), 0)

    def test_successful_cancellation(self):
        """
        Test cancelling a reservation successfully.
        """
        # Create a reservation first
        table = Table.objects.get(table_number=1)
        reservation = Reservation.objects.create(
            user=self.user,
            table=table,
            seats_booked=4,
            cost=4 * SEAT_COST
        )
        table.is_available = False
        table.save()

        url = reverse('cancel', args=[reservation.id])
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        reservation.refresh_from_db()
        self.assertTrue(reservation.is_cancelled)
        table.refresh_from_db()
        self.assertTrue(table.is_available)

    def test_cancel_nonexistent_reservation(self):
        """
        Test cancelling a reservation that does not exist.
        """
        url = reverse('cancel', args=[999]) # Nonexistent reservation ID
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['error'], 'Reservation not found or already cancelled.')

    def test_cancel_already_cancelled_reservation(self):
        """
        Test cancelling a reservation that has already been cancelled.
        """
        # Create a cancelled reservation
        table = Table.objects.get(table_number=1)
        reservation = Reservation.objects.create(
            user=self.user,
            table=table,
            seats_booked=4,
            cost=4 * SEAT_COST,
            is_cancelled=True
        )

        url = reverse('cancel', args=[reservation.id])
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['error'], 'Reservation not found or already cancelled.')

    def test_booking_unauthenticated(self):
        """
        Test booking without authentication.
        """
        self.client.logout() # Log out the user
        url = reverse('book')
        data = {'number_of_individuals': 2}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cancel_unauthenticated(self):
        """
        Test cancelling without authentication.
        """
        # Create a reservation first
        table = Table.objects.get(table_number=1)
        reservation = Reservation.objects.create(
            user=self.user,
            table=table,
            seats_booked=4,
            cost=4 * SEAT_COST
        )
        table.is_available = False
        table.save()

        self.client.logout() # Log out the user
        url = reverse('cancel', args=[reservation.id])
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

