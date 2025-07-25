import os
from dotenv import load_dotenv
import requests
import re

load_dotenv()

BACKEND_MAP_API = os.getenv("BACKEND_MAP_API")

def extract_from_itinerary(iti_txt): 
    """
    Extracts potential place names from an itinerary text.
    Assumes format: "9am–11am - Central Park"
    """
    lines = iti_txt.splitlines()
    places = []

    # parses each line for a dash and extracts the place name
    for line in lines:
        match = re.split(r'-', line, maxsplit=1)
        if len(match) >= 2:
            place = match[1].strip()
            if place:
                places.append(place)
    return places

def process_result(result):
    """
    Processes a single result from Google Places API.
    Returns a dictionary with name, address, coordinates, and Google Maps URL.
    """
    geometry = result.get("geometry", {}).get("location", {})
    return {
        "name": result.get("name"),
        "address": result.get("formatted_address"),
        "location": {
            "lat": geometry.get("lat"),
            "lng": geometry.get("lng")
        },
        "rating": result.get("rating"),
        "user_ratings_total": result.get("user_ratings_total"),
        "place_id": result.get("place_id")
    }

def get_place_details(place_name, city):
    """
    Searches for a place using Google Places API and returns 
    name, address, coordinates, and a Google Maps URL.
    """
    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    
    
    query = f"{place_name} in {city}".strip()
    params = {
        "query": query,  # Use 'query' parameter instead of 'q'
        "key": BACKEND_MAP_API
    }
    
    print(f"DEBUG: Query string: '{query}'")
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        print(f"DEBUG: Status: {response.status_code}, Response: {data}")
        
        if response.status_code == 200 and data.get("status") == "OK" and data.get("results"):
            place = data["results"][0]
            return process_result(place)

        else:
            print(f"DEBUG: API Error - Status: {data.get('status')}, Message: {data.get('error_message')}")
            
    except Exception as e:
        print(f"DEBUG: Exception occurred: {e}")
    
    return None
    
def get_places_from_itinerary(itinerary, city):
    """
    Extracts place names from an itinerary and retrieves their map details.
    """
    place_names = extract_from_itinerary(itinerary)
    places = []
    
    for place_name in place_names:
        if place_name.strip():
            place_details = get_place_details(place_name, city)
            if place_details:  # Only add if we got valid data
                places.append(place_details)
    
    return places

def get_places_from_city(city):
    """
    Retrieves a list of attractions in a given city using Google Places API.
    """
    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {
        "query": f"Things to do in {city}",
        "key": BACKEND_MAP_API
    }
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        if response.status_code == 200 and data.get("status") == "OK":
            places = [process_result(place) for place in data.get("results", [])]
            return places
        else:
            print(f"DEBUG: API Error - Status: {data.get('status')}, Message: {data.get('error_message')}")
    
    except Exception as e:
        print(f"DEBUG: Exception occurred: {e}")
    
    return []