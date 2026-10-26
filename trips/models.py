from django.contrib.auth.models import User
from django.db import models


class Trip(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="trips")
    destination = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()
    budget = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["start_date"]

    def __str__(self):
        return f"{self.destination} ({self.start_date})"

    @property
    def days(self):
        return (self.end_date - self.start_date).days + 1

    @property
    def spent(self):
        return sum((e.amount for e in self.expenses.all()), 0)

    @property
    def remaining(self):
        return self.budget - self.spent


class Activity(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name="activities")
    day = models.PositiveIntegerField(help_text="Day number within the trip (1 = first day)")
    title = models.CharField(max_length=150)
    place = models.CharField(max_length=150, blank=True, help_text="Optional place name to show on the map")
    notes = models.CharField(max_length=300, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    class Meta:
        ordering = ["day", "id"]
        verbose_name_plural = "activities"

    def __str__(self):
        return f"Day {self.day}: {self.title}"


class Expense(models.Model):
    CATEGORIES = [
        ("stay", "Stay"),
        ("food", "Food"),
        ("transport", "Transport"),
        ("activities", "Activities"),
        ("shopping", "Shopping"),
        ("other", "Other"),
    ]
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name="expenses")
    category = models.CharField(max_length=20, choices=CATEGORIES, default="other")
    description = models.CharField(max_length=150)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        return f"{self.description}: {self.amount}"
