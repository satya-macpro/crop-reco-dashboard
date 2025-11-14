# backend/app.py
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from flask_cors import CORS


import logging
try:
    from services.weather import fetch_weather
except Exception:
    fetch_weather = None

try:
    from services.soil import fetch_soil
except Exception:
    fetch_soil = None

try:
    from logic.recommender import recommend_crops
except Exception:
    recommend_crops = None

logger = logging.getLogger("crop-backend")
app = Flask(__name__)
load_dotenv()   # optional: will load backend/.env if present
CORS(app)       # allow frontend to call this API during development



@app.route("/")
def root():
    return jsonify({"message": "Crop Reco Backend. Use /health or /api/analyze"}), 200

@app.route("/health")
def health():
    return jsonify({"ok": True}), 200

@app.route("/api/analyze")

def analyze():
    lat = request.args.get("lat")
    lon = request.args.get("lon")
    if not lat or not lon:
        return jsonify({"error":"please provide lat and lon (example: /api/analyze?lat=26.85&lon=80.95)"}), 400

    # 1) try to fetch real weather and soil (safe fallbacks)
    def _safe_fetch_weather(lat, lon):
        if callable(fetch_weather):
            try:
                return fetch_weather(lat, lon)
            except Exception as e:
                logger.exception("fetch_weather failed: %s", e)
        # fallback sample 14-day
        return {"daily":[{"dt": 1700000000 + i * 86400, "rain": float((i % 3) * 5), "temp": {"day": 20 + (i % 5)}} for i in range(14)]}

    def _safe_fetch_soil(lat, lon):
        if callable(fetch_soil):
            try:
                return fetch_soil(lat, lon)
            except Exception as e:
                logger.exception("fetch_soil failed: %s", e)
        return {"ph": 6.5, "raw": None}

    weather = _safe_fetch_weather(lat, lon)
    soil = _safe_fetch_soil(lat, lon)

    # 2) if recommender is available, use it
    if callable(recommend_crops):
        try:
            rec = recommend_crops(weather, soil)
            response = {
                "location": {"lat": lat, "lon": lon},
                "weather_summary": rec.get("weather_summary"),
                "soil_summary": rec.get("soil_summary"),
                "recommendations": rec.get("scores")
            }
            return jsonify(response), 200
        except Exception as e:
            logger.exception("recommend_crops failed: %s", e)
            # fall through to fallback stub

    # 3) fallback: keep your existing stub behaviour (safe)
    sample_daily = weather.get("daily", [])[:14]
    rainfall_14d = sum(float(d.get("rain", 0)) for d in sample_daily)
    temps = []
    for d in sample_daily:
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
    mean_temp = sum(temps)/len(temps) if temps else None
    soil_ph = soil.get("ph") if isinstance(soil, dict) else soil

    # reuse your earlier simple scoring
    crops = {
        "Rice": {"rain_pref": "high"},
        "Wheat": {"rain_pref": "moderate"},
        "Millet": {"rain_pref": "low"}
    }
    scores = []
    for crop, meta in crops.items():
        if meta["rain_pref"] == "high":
            score = min(1.0, (rainfall_14d or 0) / 100.0)
        elif meta["rain_pref"] == "moderate":
            score = 0.5
        else:
            score = max(0.0, 1.0 - (rainfall_14d or 0) / 100.0)
        scores.append({
            "crop": crop,
            "score": round(score, 3),
            "reason": f"rain_14d={rainfall_14d}, mean_temp={round(mean_temp,1) if mean_temp is not None else 'N/A'}, ph={soil_ph}"
        })

    scores = sorted(scores, key=lambda x: x["score"], reverse=True)

    return jsonify({
        "location": {"lat": lat, "lon": lon},
        "weather": {"summary": {"rain_14d": rainfall_14d, "mean_temp": mean_temp}, "daily": sample_daily},
        "soil": soil,
        "recommendations": scores
    }), 200


if __name__ == "__main__":
    # debug mode auto-restarts on changes; okay for development
    app.run(host="0.0.0.0", port=5000, debug=True)
