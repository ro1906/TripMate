from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from . import services
from .forms import ActivityForm, ExpenseForm, RegisterForm, TripForm
from .models import Activity, Expense, Trip


def register(request):
    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        login(request, form.save())
        return redirect("trip_list")
    return render(request, "registration/register.html", {"form": form})


@login_required
def trip_list(request):
    return render(request, "trips/trip_list.html", {"trips": request.user.trips.all()})


@login_required
def trip_create(request):
    form = TripForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        trip = form.save(commit=False)
        trip.owner = request.user
        coords = services.geocode(trip.destination)
        if coords:
            trip.latitude, trip.longitude = coords
        trip.save()
        return redirect("trip_detail", pk=trip.pk)
    return render(request, "trips/trip_form.html", {"form": form})


def _own_trip(request, pk):
    """Only the owner can see or change a trip."""
    return get_object_or_404(Trip, pk=pk, owner=request.user)


@login_required
def trip_detail(request, pk):
    trip = _own_trip(request, pk)
    activities = list(trip.activities.all())
    by_day = [(d, [a for a in activities if a.day == d]) for d in range(1, trip.days + 1)]
    weather = services.get_weather(trip.latitude, trip.longitude, trip.start_date, trip.end_date)
    markers = [
        {"title": a.title, "place": a.place, "lat": a.latitude, "lng": a.longitude, "day": a.day}
        for a in activities if a.latitude is not None
    ]
    spent_by_category = {}
    for e in trip.expenses.all():
        label = e.get_category_display()
        spent_by_category[label] = spent_by_category.get(label, 0) + e.amount
    percent = min(100, round(trip.spent / trip.budget * 100)) if trip.budget else 0
    context = {
        "trip": trip,
        "by_day": by_day,
        "weather": weather,
        "packing": services.build_packing_list(trip.days, weather),
        "guide": services.find_local_guide(trip.destination),
        "markers": markers,
        "center": [trip.latitude, trip.longitude] if trip.latitude is not None else None,
        "activity_form": ActivityForm(trip=trip),
        "expense_form": ExpenseForm(),
        "spent_by_category": spent_by_category,
        "percent": percent,
        "over_budget": trip.budget and trip.spent > trip.budget,
    }
    return render(request, "trips/trip_detail.html", context)


@login_required
@require_POST
def trip_delete(request, pk):
    _own_trip(request, pk).delete()
    return redirect("trip_list")


@login_required
@require_POST
def activity_add(request, pk):
    trip = _own_trip(request, pk)
    form = ActivityForm(request.POST, trip=trip)
    if form.is_valid():
        activity = form.save(commit=False)
        activity.trip = trip
        if activity.place:
            coords = services.geocode(activity.place, context=trip.destination)
            if coords:
                activity.latitude, activity.longitude = coords
        activity.save()
    else:
        messages.error(request, " ".join(e for errs in form.errors.values() for e in errs))
    return redirect("trip_detail", pk=trip.pk)


@login_required
@require_POST
def activity_delete(request, pk, activity_id):
    trip = _own_trip(request, pk)
    get_object_or_404(Activity, pk=activity_id, trip=trip).delete()
    return redirect("trip_detail", pk=trip.pk)


@login_required
@require_POST
def expense_add(request, pk):
    trip = _own_trip(request, pk)
    form = ExpenseForm(request.POST)
    if form.is_valid():
        expense = form.save(commit=False)
        expense.trip = trip
        expense.save()
    else:
        messages.error(request, " ".join(e for errs in form.errors.values() for e in errs))
    return redirect("trip_detail", pk=trip.pk)


@login_required
@require_POST
def expense_delete(request, pk, expense_id):
    trip = _own_trip(request, pk)
    get_object_or_404(Expense, pk=expense_id, trip=trip).delete()
    return redirect("trip_detail", pk=trip.pk)

