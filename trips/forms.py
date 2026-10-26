from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Activity, Expense, Trip


class DateInput(forms.DateInput):
    input_type = "date"


class TripForm(forms.ModelForm):
    class Meta:
        model = Trip
        fields = ["destination", "start_date", "end_date", "budget"]
        widgets = {"start_date": DateInput(), "end_date": DateInput()}

    def clean(self):
        data = super().clean()
        start, end = data.get("start_date"), data.get("end_date")
        if start and end and end < start:
            raise forms.ValidationError("End date cannot be before the start date.")
        if data.get("budget") is not None and data["budget"] < 0:
            raise forms.ValidationError("Budget cannot be negative.")
        return data


class ActivityForm(forms.ModelForm):
    class Meta:
        model = Activity
        fields = ["day", "title", "place", "notes"]

    def __init__(self, *args, trip=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.trip = trip

    def clean_day(self):
        day = self.cleaned_data["day"]
        if self.trip and not 1 <= day <= self.trip.days:
            raise forms.ValidationError(f"Day must be between 1 and {self.trip.days}.")
        return day


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ["category", "description", "amount"]

    def clean_amount(self):
        amount = self.cleaned_data["amount"]
        if amount <= 0:
            raise forms.ValidationError("Amount must be greater than zero.")
        return amount


class RegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ["username"]
