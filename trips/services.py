"""External integrations and small pieces of business logic.

Everything here fails soft: if an API is down or slow, the page still renders
without that section instead of crashing.
"""
import json
import logging
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)

TIMEOUT = 4  # seconds
GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "TripMate/1.0 (learning project)"  # Nominatim's policy requires an identifying agent
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
FORECAST_DAYS = 16  # Open-Meteo's free forecast horizon

GUIDES_FILE = Path(__file__).parent / "data" / "local_guides.json"


def _get_json(url, params):
    request = Request(f"{url}?{urlencode(params)}", headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=TIMEOUT) as resp:
        return json.load(resp)


def _open_meteo_geocode(name):
    data = _get_json(GEOCODE_URL, {"name": name, "count": 1, "language": "en"})
    result = (data.get("results") or [None])[0]
    return (result["latitude"], result["longitude"]) if result else None


def _nominatim_geocode(query):
    data = _get_json(NOMINATIM_URL, {"q": query, "format": "json", "limit": 1})
    return (float(data[0]["lat"]), float(data[0]["lon"])) if data else None


def geocode(name, context=None):
    """Return (lat, lon) for a place name, or None if not found/unavailable.

    - Destination (no context): Open-Meteo first (good for cities), then OpenStreetMap.
    - Activity place (context = trip destination): OpenStreetMap search for
      "place, destination", so small villages and landmarks resolve in the right area.
      We do not fall back to a bare name, because a pin in the wrong region is worse than none.
    """
    if not name:
        return None
    try:
        if context:
            return _nominatim_geocode(f"{name}, {context}")
        return _open_meteo_geocode(name) or _nominatim_geocode(name)
    except Exception as exc:  # network, timeout, bad JSON...
        logger.warning("Geocoding failed for %r: %s", name, exc)
        return None


def get_weather(lat, lon, start, end, today=None):
    """Daily forecast for the part of the trip that falls inside the forecast window.

    Returns a list of dicts, or [] when there is nothing to show.
    """
    today = today or date.today()
    last_day = today + timedelta(days=FORECAST_DAYS - 1)
    first, last = max(start, today), min(end, last_day)
    if lat is None or lon is None or first > last:
        return []
    try:
        data = _get_json(
            FORECAST_URL,
            {
                "latitude": lat,
                "longitude": lon,
                "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
                "timezone": "auto",
                "start_date": first.isoformat(),
                "end_date": last.isoformat(),
            },
        )
        d = data["daily"]
        return [
            {"date": d["time"][i], "max": d["temperature_2m_max"][i],
             "min": d["temperature_2m_min"][i], "rain": d["precipitation_sum"][i]}
            for i in range(len(d["time"]))
        ]
    except Exception as exc:
        logger.warning("Weather fetch failed: %s", exc)
        return []


def build_packing_list(days, weather):
    """Rule-based packing list from trip length and (optional) forecast."""
    items = {
        "Essentials": ["ID / passport", "Tickets & bookings (offline copy)", "Phone + charger",
                       "Power bank", "Wallet / some cash", "Basic medicines"],
        "Clothes": [f"{min(days, 7)} sets of daily wear", "Comfortable walking shoes", "Sleepwear"],
        "Toiletries": ["Toothbrush & paste", "Sunscreen", "Hand sanitizer"],
    }
    if days > 7:
        items["Clothes"].append("Plan a laundry stop (long trip)")
    if weather:
        hottest = max(w["max"] for w in weather if w["max"] is not None)
        coldest = min(w["min"] for w in weather if w["min"] is not None)
        rainy = sum(1 for w in weather if (w["rain"] or 0) >= 2)
        extras = []
        if rainy:
            extras += ["Umbrella / rain jacket", "Waterproof bag cover"]
        if hottest >= 32:
            extras += ["Hat / cap", "Sunglasses", "Light cotton clothes", "Reusable water bottle"]
        if coldest <= 12:
            extras += ["Jacket / sweater", "Warm socks"]
        if extras:
            items["Weather-based"] = extras
    return items


def load_guides():
    with open(GUIDES_FILE, encoding="utf-8") as f:
        return json.load(f)


def find_local_guide(destination):
    """Match a destination string (e.g. 'Jaipur, India') to curated food/craft info."""
    text = (destination or "").lower()
    guides = load_guides()
    for key, guide in guides.items():
        names = [key] + guide.get("aliases", [])
        if any(n in text for n in names):
            return {"city": guide["display"], **guide}
    return None