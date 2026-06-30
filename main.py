import os
import requests
from fastapi import FastAPI
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("OPENWEATHER_API_KEY")

app = FastAPI()

# --- ENDPOINT 1: Current AQI ---
@app.get("/aqi")
def get_city_aqi(city: str):
    geo_url = f"http://api.openweathermap.org/geo/1.0/direct?q={city}&limit=1&appid={API_KEY}"
    geo_data = requests.get(geo_url).json()

    if not geo_data:
        return {"error": "City not found"}

    lat, lon = geo_data[0]['lat'], geo_data[0]['lon']
    aqi_url = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={API_KEY}"
    aqi_response = requests.get(aqi_url).json()

    # Extract PM2.5 to calculate the 0-500 scale number
    pm25 = aqi_response['list'][0]['components']['pm2_5']
    aqi_reading = int(pm25 * 2.5) 
    
    # Determine Safety
    if aqi_reading <= 50:
        safety, status = "Safe", "Good"
    elif aqi_reading <= 100:
        safety, status = "Moderate", "Fair"
    elif aqi_reading <= 150:
        safety, status = "Unhealthy for Sensitive Groups", "Poor"
    else:
        safety, status = "Dangerous", "Very Poor"

    return {
        "city": city,
        "lat": lat,
        "lon": lon,
        "aqi_reading": aqi_reading,
        "status": status,
        "safety": safety,
        "pollutants": aqi_response['list'][0]['components']
    }

# --- ENDPOINT 2: 5-Day Forecast ---
@app.get("/forecast")
def get_aqi_forecast(city: str):
    geo_url = f"http://api.openweathermap.org/geo/1.0/direct?q={city}&limit=1&appid={API_KEY}"
    geo_data = requests.get(geo_url).json()
    if not geo_data: return {"error": "City not found"}
    
    lat, lon = geo_data[0]['lat'], geo_data[0]['lon']
    forecast_url = f"http://api.openweathermap.org/data/2.5/air_pollution/forecast?lat={lat}&lon={lon}&appid={API_KEY}"
    res = requests.get(forecast_url).json()
    
    daily_forecast = []
    # Taking data point every 24 hours
    for entry in res['list'][::24]:
        pm25 = entry['components']['pm2_5']
        # Apply the same 0-500 scale math here
        us_aqi_reading = int(pm25 * 2.5) 
        
        daily_forecast.append({
            "date": entry['dt'],
            "aqi_score": us_aqi_reading, # The 0-500 number
            "pm2_5": pm25
        })
    
    return {"forecast": daily_forecast}