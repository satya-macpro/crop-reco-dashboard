# backend/services/soil.py
import requests

# SoilGrids public query endpoint (ISRIC). No API key required for basic queries.
SOIL_URL = "https://rest.isric.org/soilgrids/v2.0/properties/query"

def fetch_soil(lat, lon):
    """
    Query SoilGrids for soil properties at given lat/lon.
    If the network call fails or the response shape is unexpected,
    returns a safe fallback with a neutral pH.
    """
    # fallback
    fallback = {"raw": None, "ph": 6.5}

    try:
        params = {"lat": lat, "lon": lon}
        r = requests.get(SOIL_URL, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()

        # Best-effort extraction for surface pH. The real API structure can vary,
        # so inspect `data` later and adapt parsing.
        ph = None
        try:
            # SoilGrids stores properties in nested objects; attempt safe extraction
            props = data.get("properties", {})
            # try common keys that may exist
            if "phh2o" in props:
                ph = props.get("phh2o", {}).get("mean")
        except Exception:
            ph = None

        return {"raw": data, "ph": ph if ph is not None else 6.5}
    except Exception:
        return fallback
