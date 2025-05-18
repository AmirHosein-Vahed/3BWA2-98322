from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Table(models.Model):
    """
    Represents a table in the restaurant.
    """
    table_number = models.IntegerField(unique=True)
    seats = models.IntegerField()
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return f"Table {self.table_number} ({self.seats} seats)"
    
