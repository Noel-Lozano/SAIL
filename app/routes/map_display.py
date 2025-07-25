import os
from flask import render_template, request, Blueprint, jsonify, session
from app.api.map_api import get_places_from_city
from app.models.db_utils import save_place, get_user_places, delete_place
from app.models.models import Place
from datetime import datetime



map_display_bp = Blueprint('map_display', __name__)

FRONTEND_MAP_API = os.getenv("FRONTEND_MAP_API")

@map_display_bp.route("/planning")
def planning():
    city = request.args.get('city', 'New York')
    place = request.args.get('place', '')
    page_n = request.args.get('page', 1, type=int)
    places = get_places_from_city(city, place, page_n) or []

    return render_template("planning.html", places=places, google_maps_api_key=FRONTEND_MAP_API, city=city, place=place)


@map_display_bp.route("/save_place", methods=['POST'])
def save_place_route():
    if 'user_id' not in session:
        return jsonify({"error": "Please log in to save places"}), 401
    
    data = request.get_json()
    user_id = session['user_id']

    # Check if place already exists for this user
    existing_place = Place.query.filter_by(
        user_id=user_id,
        name=data['name'],
        city=data['city'],
        latitude=data['latitude'],
        longitude=data['longitude']
    ).first()
    
    if existing_place:
        return jsonify({"error": "Place already saved"}), 400

    try:
        saved_place = save_place(
            user_id=user_id,
            name=data['name'],
            city=data['city'],
            country=data.get('country', 'Unknown'),
            address=data['address'],
            latitude=data['latitude'],
            longitude=data['longitude']
        )
        return jsonify({"message": "Place saved successfully", "place_id": saved_place.id}), 201
    except Exception as e:
        return jsonify({"error": "Failed to save place"}), 500



@map_display_bp.route("/saved_places")
def saved_places():
    if 'user_id' not in session:
        return render_template("login.html", message="Please log in to view saved places")
    
    user_id = session['user_id']
    
    # Get filter parameters
    selected_city = request.args.get('city', '')
    selected_country = request.args.get('country', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    
    # Convert date strings to datetime objects for filtering
    date_from_obj = None
    date_to_obj = None
    
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
            # Add one day to include the entire day
            date_to_obj = date_to_obj.replace(hour=23, minute=59, second=59)
        except ValueError:
            pass
    
    # Get filtered places using the db_utils function
    places = get_user_places(
        user_id=user_id,
        city=selected_city if selected_city else None,
        country=selected_country if selected_country else None,
        date_from=date_from_obj,
        date_to=date_to_obj
    )
    
    # Get all places for filter options (unfiltered)
    all_places = get_user_places(user_id=user_id)
    
    # Get unique cities and countries for filter dropdowns
    cities = sorted(list(set(place.city for place in all_places)))
    countries = sorted(list(set(place.country for place in all_places if place.country)))
    
    # Group filtered places by city
    places_by_city = {}
    for place in places:
        if place.city not in places_by_city:
            places_by_city[place.city] = []
        places_by_city[place.city].append(place)
    
    # Sort cities by number of places (descending)
    places_by_city = dict(sorted(places_by_city.items(), 
                                key=lambda x: len(x[1]), reverse=True))
    
    return render_template("saved_places.html",
                         places=places,
                         places_by_city=places_by_city,
                         cities=cities,
                         countries=countries,
                         selected_city=selected_city,
                         selected_country=selected_country,
                         date_from=date_from,
                         date_to=date_to,
                         total_places=len(places))


@map_display_bp.route("/delete_place/<int:place_id>", methods=['DELETE'])
def delete_place_route(place_id):
    if 'user_id' not in session:
        return jsonify({"error": "Please log in to delete places"}), 401
    
    user_id = session['user_id']
    
    # Find the place and verify it belongs to the user
    place = Place.query.filter_by(id=place_id, user_id=user_id).first()
    
    if not place:
        return jsonify({"error": "Place not found or access denied"}), 404
    
    try:
        delete_place(place_id)
        return jsonify({"message": "Place deleted successfully"}), 200
    except Exception as e:
        return jsonify({"error": "Failed to delete place"}), 500