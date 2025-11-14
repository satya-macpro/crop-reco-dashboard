# backend/app.py
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/")
def root():
    return jsonify({"message": "Crop Reco Backend. Use /health or /api/analyze"}), 200

@app.route("/health")
def health():
    return jsonify({"ok": True}), 200

@app.route("/api/analyze")
def analyze():
    """
    Simple stubbed analyze endpoint (no external APIs).
    Accepts query params: lat and lon.
    Returns sample weather, soil, and recommendation structure so frontend can work.
    """
    lat = request.args.get("lat", "unknown")
    lon = request.args.get("lon", "unknown")

    # SAMPLE (stubbed) weather data (14 days)
    sample_daily = [
        {"dt": 1700000000 + i * 86400, "rain": float(i % 3 * 5), "temp": {"day": 20 + (i % 5)}}
        for i in range(14)
    ]
    weather = {"daily": sample_daily}

    # SAMPLE soil data
    soil = {"ph": 6.5}

    # SIMPLE recommendation logic (stub; mirrors later recommender)
    # This is a tiny scoring example so frontend can display information now.
    rainfall_14d = sum(d.get("rain", 0) for d in sample_daily)
    mean_temp = sum(d["temp"]["day"] for d in sample_daily) / len(sample_daily)

    scores = []
    # Example crops
    crops = {
        "Rice": {"rain_pref": "high"},
        "Wheat": {"rain_pref": "moderate"},
        "Millet": {"rain_pref": "low"}
    }
    for crop, meta in crops.items():
        # fake score: Rice prefers higher rainfall, Millet prefers low
        if meta["rain_pref"] == "high":
            score = min(1.0, rainfall_14d / 100.0)
        elif meta["rain_pref"] == "moderate":
            score = 0.5
        else:
            score = max(0.0, 1.0 - rainfall_14d / 100.0)
        scores.append({
            "crop": crop,
            "score": round(score, 3),
            "reason": f"rain_14d={rainfall_14d}, mean_temp={round(mean_temp,1)}, ph={soil['ph']}"
        })

    # sort descending
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
