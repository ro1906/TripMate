# 🧭 TripMate: a simple trip planner

Plan a trip day by day, track the budget, check the weather, see your plans on a map,
get a packing list, and discover the **local food and arts & crafts** of your destination.

**Stack:** Python · Django · SQLite · HTML/CSS/JavaScript · Leaflet (OpenStreetMap) · Open-Meteo API

## Features
- **Accounts:** sign up / log in; every user only sees their own trips
- **Itinerary:** day-wise activities, with an optional place name that is geocoded and pinned on the map
- **Budget tracker:** expenses by category, progress bar, over-budget warning
- **Weather:** live daily forecast for the destination (Open-Meteo, no API key)
- **Packing list:** generated from trip length and the forecast (rain, heat, cold)
- **Local flavours:** must-try food and local crafts for the destination (curated, info-only)

## Run it
```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver        # open http://127.0.0.1:8000
python manage.py test             # 12 tests
```
Optional: `python manage.py createsuperuser` to use `/admin/`.

## How it is built
| File | Purpose |
|---|---|
| `trips/models.py` | `Trip`, `Activity`, `Expense` (relational schema, foreign keys) |
| `trips/views.py` | Views; every trip lookup is filtered by `owner=request.user` |
| `trips/forms.py` | Validation (dates, budget, day range, amount > 0) |
| `trips/services.py` | Open-Meteo geocoding and weather, packing rules, local guide lookup |
| `trips/data/local_guides.json` | Curated food and craft data for 13 cities |
| `trips/tests.py` | Model/view/service tests; external APIs are mocked |

## Design decisions (good interview answers)
- **Third-party APIs fail soft.** Short timeouts and try/except, so a weather outage never breaks the page.
- **Authorization, not just login.** Trips are fetched with `get_object_or_404(Trip, pk=pk, owner=request.user)`, so other users get 404.
- **Destructive actions are POST-only** with CSRF protection.
- **No API keys needed**, so anyone can clone and run it.
- **Curated JSON for local food/crafts** keeps the data accurate and offline; a possible next step is an LLM endpoint for destinations not in the file.

## Ideas for later
REST API with Django REST Framework + React frontend · LLM "suggest activities" · Docker + CI · deploy on Render
