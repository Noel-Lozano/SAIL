import json
import os
from dotenv import load_dotenv
import requests
import ast
import populartimes

load_dotenv()

BACKEND_MAP_API = os.getenv("BACKEND_MAP_API")
disabled = True # save API calls during development

# [38, 64, 82, 90, 89, 81, 64, 41, 100, 100, 100, 100, 100, 100, 100] Statue of Liberty
# [50, 69, 81, 86, 86, 86, 83, 81, 80, 79, 79, 76, 68, 52, 33] SUMMIT One Vanderbilt
# [19, 30, 40, 50, 58, 64, 68, 73, 77, 83, 91, 97, 100, 92, 75] Times Square
# [100, 34, 53, 72, 87, 97, 100, 94, 82, 67, 50, 34, 100, 100, 100] The Metropolitan Museum of Art

def get_popularity(place_id):
    if disabled:
        print("DEBUG: Disabled mode is ON, returning dummy data.")
        return [{'name': 'Monday', 'data': [27, 13, 6, 4, 3, 3, 4, 7, 11, 16, 21, 26, 30, 33, 35, 37, 39, 43, 47, 52, 55, 55, 47, 36]}, {'name': 'Tuesday', 'data': [20, 10, 5, 3, 3, 3, 5, 7, 11, 15, 21, 25, 29, 32, 34, 37, 42, 49, 56, 61, 64, 62, 53, 38]}, {'name': 'Wednesday', 'data': [21, 10, 5, 3, 3, 3, 5, 8, 12, 17, 24, 32, 38, 42, 44, 47, 50, 53, 57, 60, 63, 62, 54, 40]}, {'name': 'Thursday', 'data': [22, 11, 5, 3, 3, 3, 5, 8, 12, 18, 24, 30, 33, 36, 39, 43, 48, 54, 61, 67, 72, 71, 62, 47]}, {'name': 'Friday', 'data': [27, 13, 6, 4, 4, 4, 5, 8, 13, 19, 25, 31, 35, 39, 43, 48, 53, 59, 68, 76, 82, 84, 77, 62]}, {'name': 'Saturday', 'data': [37, 19, 9, 5, 4, 4, 4, 7, 12, 19, 30, 40, 50, 58, 64, 68, 73, 77, 83, 91, 97, 100, 92, 75]}, {'name': 'Sunday', 'data': [46, 24, 11, 6, 4, 3, 4, 6, 10, 17, 25, 34, 42, 49, 55, 60, 65, 67, 69, 70, 71, 69, 60, 46]}]
    data = populartimes.get_id(BACKEND_MAP_API, place_id)
    return data.get("populartimes", [])

def process_result(result):
    """
    Processes a single result from Google Places API.
    Returns a dictionary with name, address, coordinates, Google Maps URL, etc.
    """
    name = result.get("displayName", {}).get("text", "No Name Provided")
    address = result.get("formattedAddress", "No Address Provided")
    location = result.get("location", {})
    lat = location.get("latitude", 0.0)
    lng = location.get("longitude", 0.0)
    place_id = result.get("id", "No ID Provided")
    rating = result.get("rating", "No Rating Provided")
    user_rating_count = result.get("userRatingCount", "No User Rating Count Provided")
    editorial_summary = result.get("editorialSummary", {}).get("text", "No Summary Provided")
    google_maps_uri = result.get("googleMapsUri", "No URI Provided")
    open_hours = result.get("regularOpeningHours", {}).get("periods", [])

    return {
        "name": name,
        "address": address,
        "location": {"lat": lat, "lng": lng},
        "place_id": place_id,
        "rating": rating,
        "user_rating_count": user_rating_count,
        "editorial_summary": editorial_summary,
        "google_maps_uri": google_maps_uri,
        "open_hours": open_hours
    }

cache = {}

def get_places_from_city(city, place, page_n = 1):
    if disabled:
        print("DEBUG: Disabled mode is ON, returning dummy data.")
        with open("app/api/new_york.txt", "r", encoding="utf-8") as file:
            data = ast.literal_eval(file.read())
            return [process_result(place) for place in data.get("places", [])]

    identifier = f"{city}_{place}"
    print(f"DEBUG: Identifier for cache: {identifier}")
    pageToken = None
    if identifier in cache and page_n < cache[identifier]["next_page"]:
        print("DEBUG: Cache hit for identifier:", identifier)
        return cache[identifier]["pages"][page_n]
    else:
        if identifier in cache and page_n == cache[identifier]["next_page"] and cache[identifier]["next_page_token"]:
            cache[identifier]["next_page"] += 1
            pageToken = cache[identifier]["next_page_token"]
        elif identifier not in cache:
            cache[identifier] = {
                "next_page": 2,
                "pages": {}
            }
        else:
            return []
    

    url = "https://places.googleapis.com/v1/places:searchText"
    payload = {
        "textQuery": f"Things to do in {city}"
    }
    if place:
        payload["textQuery"] = f"{place} in {city}"
    if pageToken:
        payload["pageToken"] = pageToken
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": BACKEND_MAP_API,
        "X-Goog-FieldMask": "places.id,places.displayName,places.location,places.formattedAddress,places.rating,places.userRatingCount,places.editorialSummary,places.googleMapsUri,nextPageToken"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        data = response.json()
        
        if response.status_code == 200:
            places = [process_result(place) for place in data.get("places", [])]
            cache[identifier]["pages"][page_n] = places
            cache[identifier]["next_page_token"] = data.get("nextPageToken", None)
            return places
        else:
            print(f"DEBUG: API Error - Status: {data.get('status')}, Message: {data.get('error_message')}")
    
    except Exception as e:
        print(f"DEBUG: Exception occurred: {e}")
    
    return []