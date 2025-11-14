# backend/tests/test_recommender.py
from logic.recommender import recommend_crops

def test_recommender_runs():
    fake_weather = {"daily":[{"rain":5,"temp":{"day":25}} for _ in range(14)]}
    fake_soil = {"ph": 6.5}
    out = recommend_crops(fake_weather, fake_soil)
    assert "scores" in out
    assert isinstance(out["scores"], list)
