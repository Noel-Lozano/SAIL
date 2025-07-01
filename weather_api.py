import os
from dotenv import load_dotenv
import requests

# Load environment variables from .env file
load_dotenv()


WEATHER_API = os.getenv("WEATHER_API")

def get_weather(city, target_date):
    """Fetches the weather forecast for a given city on a specific date."""
    
    weather_url = f"https://api.openweathermap.org/data/2.5/forecast" # 5-day/3-hour forecast url
    
    params = { # parameters for the API request
        "q" : city,
        "appid": WEATHER_API,
        "units": "metric"
    }

    response = requests.get(weather_url, params=params) # make the API request
    data = response.json() # parse the JSON response

    if response.status_code == 200: # if response is successful
        # Convert target_date to the format used in the API response
        for item in data["list"]:
            if item["dt_txt"].startswith(target_date):
                return {
                    "temperature": item["main"]["temp"],
                }
               
    return {"error": "Weather data not found"}

