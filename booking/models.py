from django.db import models
from django.contrib.auth.models import User

SEAT_COST = 10  # Example seat cost
MIN_SEATS_PER_TABLE = 4
MAX_SEATS_PER_TABLE = 10
TOTAL_TABLES = 10 # As per the document

# Create your models here.
class Table(models.Model):
    """
    Represents a table in the restaurant.
    """
    table_number = models.IntegerField(unique=True)
    seats = models.IntegerField(validators=[
        models.validators.MinValueValidator(MIN_SEATS_PER_TABLE),
        models.validators.MaxValueValidator(MAX_SEATS_PER_TABLE)
    ])
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return f"Table {self.table_number} ({self.seats} seats)"
    
class Reservation(models.Model):
    """
    Represents a reservation made by a user.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    table = models.ForeignKey(Table, on_delete=models.CASCADE)
    seats_booked = models.IntegerField()
    cost = models.DecimalField(max_digits=10, decimal_places=2)
    booking_time = models.DateTimeField(auto_now_add=True)
    is_cancelled = models.BooleanField(default=False)

    def __str__(self):
        return f"Reservation for {self.user.username} at Table {self.table.table_number}"