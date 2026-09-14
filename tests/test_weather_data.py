from src.data.weather.weather_data import load_weather_data
from src.app.core.weather_risk import calculate_weather_risk


def test_weather_data_loads():
    weather_data = load_weather_data()

    assert len(weather_data) == 8


def test_weather_data_has_required_fields():
    weather_data = load_weather_data()
    reading = weather_data[0]

    assert "asset_id" in reading
    assert "wind_speed" in reading
    assert "rainfall" in reading
    assert "lightning_probability" in reading
    assert "flood_risk" in reading
    assert "temperature" in reading


def test_weather_data_can_be_used_for_risk_scoring():
    weather_data = load_weather_data()
    reading = weather_data[0]

    result = calculate_weather_risk(reading)

    assert "weather_risk_score" in result
    assert "dominant_hazard" in result
    assert 0 <= result["weather_risk_score"] <= 1