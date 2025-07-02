import os
from dotenv import load_dotenv
import requests

# Load environment variables from .env file
load_dotenv()

WEATHER_API = os.getenv("WEATHER_API")


def get_weather(city, target_date):
    """Fetches the weather forecast for a given city on a specific date."""

    weather_url = "https://api.openweathermap.org/data/2.5/forecast"

    params = {
        "q": city,
        "appid": WEATHER_API,
        "units": "metric"
    }

    response = requests.get(weather_url, params=params)
    data = response.json()

    if response.status_code == 200:
        for item in data["list"]:
            if item["dt_txt"].startswith(target_date):
                return {
                    "temperature": item["main"]["temp"],
                    "description": item["weather"][0]["description"]
                }

    return {"error": "Weather data not found"}
