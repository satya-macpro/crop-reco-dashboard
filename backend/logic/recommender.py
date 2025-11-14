# backend/logic/recommender.py
"""
Simple crop recommender.
Inputs:
 - weather_json: expects 'daily' list with items containing 'rain' and 'temp':{'day':..}
 - soil_json: expects {'ph': value}
Outputs a dict with weather_summary, soil_summary, and sorted scores list.
"""

def safe_get_daily(weather_json, days=90):
    return weather_json.get("daily", [])[:days]

def compute_90day_rainfall(weather_json):
    daily = safe_get_daily(weather_json, days=90)
    return sum(float(d.get("rain", 0)) for d in daily)

def compute_mean_temp(weather_json, days=90):
    daily = safe_get_daily(weather_json, days)
    temps = []
    for d in daily:
        t = d.get("temp")
        if isinstance(t, dict):
            if t.get("day") is not None:
                temps.append(t.get("day"))
            else:
                mx = t.get("max"); mn = t.get("min")
                if mx is not None and mn is not None:
                    temps.append((mx + mn) / 2)
        elif isinstance(t, (int, float)):
            temps.append(t)
    return sum(temps)/len(temps) if temps else None

# Example rules and weights — tune later with agronomy input
CROP_RULES = {
    "Rice": {"rain_min": 800, "temp_min": None, "temp_max": 35, "ph_min": 5.0, "ph_max": 7.5},
    "Maize": {"rain_min": 400, "rain_max": 1200, "temp_min": 15, "temp_max": 35, "ph_min": 5.5, "ph_max": 7.5},
    "Wheat": {"rain_min": 300, "rain_max": 800, "temp_min": 0, "temp_max": 25, "ph_min": 6.0, "ph_max": 7.5},
    "Millet": {"rain_max": 400, "temp_min": 25, "temp_max": 40, "ph_min": 5.0, "ph_max": 8.0},
    "Soybean": {"rain_min": 500, "rain_max": 900, "temp_min": 15, "temp_max": 30, "ph_min": 6.0, "ph_max": 7.0},
    "Potato": {"rain_min": 600, "rain_max": 1200, "temp_min": 10, "temp_max": 24, "ph_min": 5.0, "ph_max": 6.5},
}

WEIGHTS = {"rainfall": 0.45, "temp": 0.35, "ph": 0.20}

def score_match(value, low=None, high=None):
    if value is None:
        return 0.0
    try:
        value = float(value)
    except Exception:
        return 0.0
    if low is not None and high is not None:
        if low <= value <= high:
            return 1.0
        span = max(1.0, high - low)
        if value < low:
            return max(0.0, 1 - (low - value) / span)
        else:
            return max(0.0, 1 - (value - high) / span)
    if low is not None:
        return 1.0 if value >= low else max(0.0, value / low)
    if high is not None:
        return 1.0 if value <= high else max(0.0, 1 - (value - high) / (high if high else 1))
    return 0.0

def recommend_crops(weather_json, soil_json):
    rainfall = compute_90day_rainfall(weather_json)
    mean_temp = compute_mean_temp(weather_json)
    ph = soil_json.get("ph") if isinstance(soil_json, dict) else None

    scores = []
    for crop, rule in CROP_RULES.items():
        r_score = score_match(rainfall, low=rule.get("rain_min"), high=rule.get("rain_max"))
        t_score = score_match(mean_temp, low=rule.get("temp_min"), high=rule.get("temp_max"))
        p_score = score_match(ph, low=rule.get("ph_min"), high=rule.get("ph_max"))
        total = (r_score * WEIGHTS["rainfall"] +
                 t_score * WEIGHTS["temp"] +
                 p_score * WEIGHTS["ph"])
        scores.append({
            "crop": crop,
            "score": round(total, 3),
            "breakdown": {"rain": round(r_score,3), "temp": round(t_score,3), "ph": round(p_score,3)},
            "reason": f"rain={round(rainfall,1) if rainfall is not None else 'N/A'}, temp={round(mean_temp,1) if mean_temp is not None else 'N/A'}, ph={ph}"
        })
    scores.sort(key=lambda x: x["score"], reverse=True)

    return {
        "weather_summary": {"90d_rainfall": rainfall, "mean_temp": mean_temp},
        "soil_summary": {"ph": ph},
        "scores": scores
    }
