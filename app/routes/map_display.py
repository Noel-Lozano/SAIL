import os
from flask import render_template, request, Blueprint
from app.api.map_api import get_places_from_city

map_display_bp = Blueprint('map_display', __name__)

FRONTEND_MAP_API = os.getenv("FRONTEND_MAP_API")

@map_display_bp.route("/planning")
def planning():
    city = request.args.get('city', 'New York')
    place = request.args.get('place', '')
    page_n = request.args.get('page', 1, type=int)
    places = get_places_from_city(city, place, page_n) or []

    return render_template("planning.html", places=places, google_maps_api_key=FRONTEND_MAP_API, city=city, place=place)