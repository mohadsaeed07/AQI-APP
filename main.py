import os
from functools import lru_cache

import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Response, status
from prometheus_fastapi_instrumentator import Instrumentator

load_dotenv()
API_KEY = os.getenv("OPENWEATHER_API_KEY")

app = FastAPI(title="AQI Microservice")

# Expose Prometheus metrics at /metrics automatically
Instrumentator().instrument(app).expose(app)

session = requests.Session()
TIMEOUT = (5, 10)


# ==========================================
# Kubernetes Health & Readiness Probes
# ==========================================
@app.get("/healthz/live", tags=["Health"])
def liveness_check():
    """Liveness probe: verifies the container process is alive."""
    return {"status": "alive"}


@app.get("/healthz/ready", tags=["Health"])
def readiness_check(response: Response):
    """Readiness probe: verifies the container is ready to handle external traffic."""
    if not API_KEY:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "unready", "reason": "Missing OPENWEATHER_API_KEY"}
    return {"status": "ready"}


# ==========================================
# Geocoding & Data Retrieval Logic
# ==========================================
@lru_cache(maxsize=128)
def get_coordinates(city: str):
    geo_url = f"https://api.openweathermap.org/geo/1.0/direct?q={city}&limit=1&appid={API_KEY}"
    try:
        res = session.get(geo_url, timeout=TIMEOUT)
        res.raise_for_status()
        geo_data = res.json()
    except requests.exceptions.Timeout:
        raise HTTPException(
            status_code=504,
            detail=f"Geocoding service timed out while looking up '{city}'.",
        )
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to communicate with geocoding service: {e!s}",
        )

    if not geo_data:
        raise HTTPException(status_code=404, detail=f"City '{city}' not found")

    return geo_data[0]["lat"], geo_data[0]["lon"]


# --- ENDPOINT 1: Current AQI ---
@app.get("/aqi")
def get_city_aqi(city: str):
    lat, lon = get_coordinates(city.strip().title())
    aqi_url = f"https://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={API_KEY}"

    try:
        res = session.get(aqi_url, timeout=TIMEOUT)
        res.raise_for_status()
        aqi_response = res.json()
    except requests.exceptions.Timeout:
        raise HTTPException(
            status_code=504,
            detail="AQI service timed out while fetching pollution data.",
        )
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to communicate with AQI service: {e!s}",
        )

    if "list" not in aqi_response or not aqi_response["list"]:
        raise HTTPException(
            status_code=502, detail="Invalid data received from weather service"
        )

    pm25 = aqi_response["list"][0]["components"]["pm2_5"]
    aqi_reading = int(pm25 * 2.5)

    if aqi_reading <= 50:
        safety, status_label = "Safe", "Good"
    elif aqi_reading <= 100:
        safety, status_label = "Moderate", "Fair"
    elif aqi_reading <= 150:
        safety, status_label = "Unhealthy for Sensitive Groups", "Poor"
    else:
        safety, status_label = "Dangerous", "Very Poor"

    return {
        "city": city,
        "lat": lat,
        "lon": lon,
        "aqi_reading": aqi_reading,
        "status": status_label,
        "safety": safety,
        "pollutants": aqi_response["list"][0]["components"],
    }


# --- ENDPOINT 2: 5-Day Forecast ---
@app.get("/forecast")
def get_aqi_forecast(city: str):
    lat, lon = get_coordinates(city.strip().title())
    forecast_url = f"https://api.openweathermap.org/data/2.5/air_pollution/forecast?lat={lat}&lon={lon}&appid={API_KEY}"

    try:
        res = session.get(forecast_url, timeout=TIMEOUT)
        res.raise_for_status()
        forecast_response = res.json()
    except requests.exceptions.Timeout:
        raise HTTPException(
            status_code=504,
            detail="Forecast service timed out while fetching forecast data.",
        )
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to communicate with forecast service: {e!s}",
        )

    if "list" not in forecast_response:
        raise HTTPException(
            status_code=502, detail="Invalid forecast data received"
        )

    daily_forecast = []
    for entry in forecast_response["list"][::24]:
        pm25 = entry["components"]["pm2_5"]
        us_aqi_reading = int(pm25 * 2.5)
        daily_forecast.append({
            "date": entry["dt"],
            "aqi_score": us_aqi_reading,
            "pm2_5": pm25,
        })

    return {"forecast": daily_forecast}