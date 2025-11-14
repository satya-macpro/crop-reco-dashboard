# backend/services/weather.py
import os
import requests

# Load key from environment; set OWM_KEY in backend/.env when ready
OWM_KEY = os.getenv("OWM_KEY")

def fetch_weather(lat, lon):
    """
    Fetch weather from OpenWeather One Call 3.0 if OWM_KEY is present.
    If OWM_KEY is missing or call fails, return a safe static sample (14-day).
    """
    # fallback sample (14 days) so frontend and recommender can work without keys
    sample = {"daily": [
        {"dt": 1700000000 + i * 86400, "rain": float((i % 3) * 4), "temp": {"day": 20 + (i % 5)}}
        for i in range(14)
    ]}

    if not OWM_KEY:
        return sample

    try:
        url = "https://api.openweathermap.org/data/3.0/onecall"
        params = {
            "lat": lat,
            "lon": lon,
            "exclude": "minutely,alerts",
            "units": "metric",
            "appid": OWM_KEY
        }
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception:
        # on any error return the safe sample
        return sample
