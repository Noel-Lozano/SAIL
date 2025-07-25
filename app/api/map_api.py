import os
from dotenv import load_dotenv
import requests
import re

load_dotenv()

BACKEND_MAP_API = os.getenv("BACKEND_MAP_API")

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

    return {
        "name": name,
        "address": address,
        "location": {"lat": lat, "lng": lng},
        "place_id": place_id,
        "rating": rating,
        "user_rating_count": user_rating_count,
        "editorial_summary": editorial_summary,
        "google_maps_uri": google_maps_uri
    }

# def get_place_details(place_name, city):
#     """
#     Searches for a place using Google Places API and returns 
#     name, address, coordinates, and a Google Maps URL.
#     """
#     url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    
    
#     query = f"{place_name} in {city}".strip()
#     params = {
#         "query": query,  # Use 'query' parameter instead of 'q'
#         "key": BACKEND_MAP_API
#     }
    
#     print(f"DEBUG: Query string: '{query}'")
    
#     try:
#         response = requests.get(url, params=params)
#         data = response.json()
        
#         print(f"DEBUG: Status: {response.status_code}, Response: {data}")
        
#         if response.status_code == 200 and data.get("status") == "OK" and data.get("results"):
#             place = data["results"][0]
#             return process_result(place)

#         else:
#             print(f"DEBUG: API Error - Status: {data.get('status')}, Message: {data.get('error_message')}")
            
#     except Exception as e:
#         print(f"DEBUG: Exception occurred: {e}")
    
#     return None
    
cache = {}

def get_places_from_city(city, place, page_n = 1):
    # check cache first

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
            print("pagenexttoken", cache[identifier]["next_page_token"])
            return places
        else:
            print(f"DEBUG: API Error - Status: {data.get('status')}, Message: {data.get('error_message')}")
    
    except Exception as e:
        print(f"DEBUG: Exception occurred: {e}")
    
    return []