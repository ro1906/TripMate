from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from . import services
from .models import Activity, Expense, Trip


class ServiceTests(TestCase):
    def test_local_guide_matches_city_and_aliases(self):
        self.assertEqual(services.find_local_guide("Jaipur, India")["city"], "Jaipur")
        self.assertEqual(services.find_local_guide("Bombay")["city"], "Mumbai")
        self.assertIsNone(services.find_local_guide("Atlantis"))

    def test_all_guides_have_food_and_crafts(self):
        for key, g in services.load_guides().items():
            self.assertTrue(g["food"] and g["crafts"], key)

    def test_packing_list_uses_weather(self):
        wet_cold = [{"date": "2026-11-01", "max": 15, "min": 8, "rain": 10}]
        extras = services.build_packing_list(3, wet_cold)["Weather-based"]
        self.assertIn("Umbrella / rain jacket", extras)
        self.assertIn("Jacket / sweater", extras)
        self.assertNotIn("Weather-based", services.build_packing_list(3, []))

    def test_weather_skipped_outside_forecast_window(self):
        today = date(2026, 10, 26)
        far = today + timedelta(days=60)
        with patch("trips.services._get_json") as api:
            self.assertEqual(services.get_weather(1, 1, far, far, today=today), [])
            api.assert_not_called()

    def test_weather_and_geocode_fail_soft(self):
        with patch("trips.services._get_json", side_effect=OSError("down")):
            self.assertIsNone(services.geocode("Goa"))
            today = date.today()
            self.assertEqual(services.get_weather(1, 1, today, today), [])


class TripFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("asha", password="pw12345!")
        self.other = User.objects.create_user("ravi", password="pw12345!")
        self.client.login(username="asha", password="pw12345!")
        self.trip = Trip.objects.create(
            owner=self.user, destination="Goa", budget=Decimal("10000"),
            start_date=date(2027, 1, 10), end_date=date(2027, 1, 12),
        )

    def test_login_required(self):
        self.client.logout()
        resp = self.client.get(reverse("trip_list"))
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/accounts/login/", resp["Location"])

    @patch("trips.views.services.geocode", return_value=(15.49, 73.83))
    def test_create_trip(self, _geo):
        resp = self.client.post(reverse("trip_create"), {
            "destination": "Jaipur", "start_date": "2027-02-01", "end_date": "2027-02-03", "budget": "5000"})
        trip = Trip.objects.get(destination="Jaipur")
        self.assertRedirects(resp, reverse("trip_detail", args=[trip.pk]))
        self.assertEqual(trip.owner, self.user)
        self.assertEqual(trip.days, 3)
        self.assertEqual(trip.latitude, 15.49)

    def test_rejects_end_before_start(self):
        resp = self.client.post(reverse("trip_create"), {
            "destination": "X", "start_date": "2027-02-05", "end_date": "2027-02-01", "budget": "1"})
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(Trip.objects.filter(destination="X").exists())

    def test_users_cannot_see_or_change_others_trips(self):
        self.client.logout()
        self.client.login(username="ravi", password="pw12345!")
        self.assertEqual(self.client.get(reverse("trip_detail", args=[self.trip.pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse("trip_delete", args=[self.trip.pk])).status_code, 404)
        self.assertTrue(Trip.objects.filter(pk=self.trip.pk).exists())

    @patch("trips.views.services.geocode", return_value=(15.55, 73.75))
    def test_add_activity_validates_day(self, _geo):
        url = reverse("activity_add", args=[self.trip.pk])
        self.client.post(url, {"day": 2, "title": "Beach", "place": "Baga Beach", "notes": ""})
        self.client.post(url, {"day": 9, "title": "Too late", "place": "", "notes": ""})
        self.assertEqual(Activity.objects.count(), 1)
        self.assertEqual(Activity.objects.get().latitude, 15.55)

    def test_budget_math_and_validation(self):
        url = reverse("expense_add", args=[self.trip.pk])
        self.client.post(url, {"category": "food", "description": "Lunch", "amount": "400"})
        self.client.post(url, {"category": "stay", "description": "Hotel", "amount": "-5"})
        self.assertEqual(Expense.objects.count(), 1)
        self.assertEqual(self.trip.spent, Decimal("400"))
        self.assertEqual(self.trip.remaining, Decimal("9600"))

    @patch("trips.views.services.get_weather", return_value=[])
    def test_detail_page_shows_local_flavours(self, _w):
        resp = self.client.get(reverse("trip_detail", args=[self.trip.pk]))
        self.assertContains(resp, "Goan fish curry rice")
        self.assertContains(resp, "Terracotta pottery")
