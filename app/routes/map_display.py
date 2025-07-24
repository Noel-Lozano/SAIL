import os
from flask import render_template, request, Blueprint
from app.api.map_api import get_places_from_itinerary, get_places_from_city

map_display_bp = Blueprint('map_display', __name__)

FRONTEND_MAP_API = os.getenv("FRONTEND_MAP_API")

@map_display_bp.route('/map')
def show_map():
    city = request.args.get('city')
    itinerary = request.args.get('itinerary') # Pass itinerary from AI

    if not city or not itinerary:
        return "City and itinerary are required", 400
    
    places = get_places_from_itinerary(itinerary, city) or []
    
    return render_template("map.html",
                           google_maps_api_key=FRONTEND_MAP_API,
                           places=places,
                           itinerary=itinerary,
                           city=city)  # Pass city to template

@map_display_bp.route("/test-map")
def test_map():
    city = "New York"
    itinerary = """9:00 AM - Central Park
11:00 AM - The Metropolitan Museum of Art
2:00 PM - Times Square
4:00 PM - Statue of Liberty
7:00 PM - Brooklyn Bridge"""
    
    places = get_places_from_itinerary(itinerary, city) or []
    
    return render_template("map.html",
                           places=places,
                           google_maps_api_key=FRONTEND_MAP_API,
                           itinerary=itinerary,
                           city=city)

@map_display_bp.route("/test-search")
def test_search():
    city = request.args.get('city', 'New York')
    places = get_places_from_city(city) or []

    return render_template("search_city.html", places=places, google_maps_api_key=FRONTEND_MAP_API, city=city)