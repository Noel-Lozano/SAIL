import os
from flask import render_template, request, Blueprint
from app.api.map_api import get_places_from_itinerary

map_display_bp = Blueprint('map_display', __name__)

@map_display_bp.route('/map')
def show_map():
    city = request.args.get('city')
    itinerary = request.args.get('itinerary') # Pass itinerary from AI

    if not city or not itinerary:
        return "City and itinerary are required", 400
    
    places = get_places_from_itinerary(itinerary, city) or []
    
    return render_template("map.html",
                           google_maps_api_key=os.getenv("FRONTEND_MAP_API"),  # Fixed variable name
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
                           google_maps_api_key=os.getenv("FRONTEND_MAP_API"),  # Consistent naming
                           itinerary=itinerary,
                           city=city)