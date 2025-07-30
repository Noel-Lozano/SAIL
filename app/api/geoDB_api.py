import requests
import os
import time
from dotenv import load_dotenv

load_dotenv()

GEODB_API_HOST = "wft-geo-db.p.rapidapi.com"
GEODB_API_KEY = os.environ.get("GEODB_KEY")

def fetch_and_save_popular_cities(filename="cities2.txt"):
    url = "https://wft-geo-db.p.rapidapi.com/v1/geo/places"
    headers = {
        "X-RapidAPI-Key": GEODB_API_KEY,
        "X-RapidAPI-Host": GEODB_API_HOST,
    }

    limit = 10
    offset = 0
    all_cities = set()
    total_count = None 

    while True:
        params = {
            "limit": limit,
            "offset": offset,
            "types": "CITY",
            "minPopulation": 1000000,
            "sort": "-population"
        }

        print(f"Fetching cities with offset {offset}...")

        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            print("Error:", response.status_code, response.text)
            break

        data = response.json()

        if total_count is None:
            total_count = data.get("metadata", {}).get("totalCount", 0)
            print(f"Total cities expected: {total_count}")

        places = data.get("data", [])

        if not places:
            print("No more cities found.")
            break

        for place in places:
            city_name = place.get("name") or place.get("city")
            if city_name:
                all_cities.add(city_name.strip())

        offset += limit
        time.sleep(2)  

        if offset >= total_count:
            break

    print(f"Fetched {len(all_cities)} unique popular cities.")
    
    with open(filename, "w", encoding="utf-8") as f:
        for city in sorted(all_cities):
            f.write(city + "\n")
    
    print(f"Saved to {filename}")

if __name__ == "__main__":
    fetch_and_save_popular_cities()
