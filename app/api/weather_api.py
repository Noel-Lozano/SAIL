import os
from dotenv import load_dotenv
import requests
from datetime import datetime, timedelta

# Load environment variables from .env file
load_dotenv()

WEATHER_API = os.getenv("WEATHER_API")

base_url = "http://api.weatherapi.com/v1/forecast.json"


def get_weather(city, start_date, end_date):
    """Fetches the weather forecast for a given city on a specific date range."""

    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    today = datetime.today()

    results = []
    curr_dt = start_dt

    while curr_dt <= end_dt:
        days_ahead = (curr_dt - today).days

        if days_ahead < 9: # Forecasts available for up to 9 days ahead
            url = f"{base_url}/forecast.json"
            params = {
                "key": WEATHER_API,
                "q": city,
                "days": 1,
                "date": curr_dt.strftime("%Y-%m-%d")
            }
        else:
            hist_dt = curr_dt.replace(year=today.year - 1)
            url = f"{base_url}/history.json"
            params = {
                "key": WEATHER_API,
                "q": city,
                "dt": hist_dt.strftime("%Y-%m-%d")
            }

        response = requests.get(url, params=params) 
        data = response.json()

        try:
            if "forecast" in data:
                day_data = data["forecast"]["forecastday"][0]["day"]
                results.append({
                    "date": curr_dt.strftime("%Y-%m-%d"),
                    "avg_temp": day_data["avgtemp_c"],
                    "description": day_data["condition"]["text"],
                    "icon": day_data["condition"]["icon"]
                    })
        except (KeyError, IndexError):
            results.append({"date": curr_dt.strftime("%Y-%m-%d"), "error": "Data not available"})

        curr_dt += timedelta(days=1)

    return results

    

print(get_weather("New York", "2025-08-04", "2025-08-07"))  # Example usage
