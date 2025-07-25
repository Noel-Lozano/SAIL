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

@map_display_bp.route("/itinerary")
def itinerary():
    if 'user_id' not in session:
        return render_template("login.html", message="Please log in to view your itinerary")

    user_id = session['user_id']
    all_places = get_user_places(user_id=user_id)
    
    return render_template("itinerary.html",
                         places=all_places,
                         total_places=len(all_places))

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
            address=data['address'],
            latitude=data['latitude'],
            longitude=data['longitude'],
            editorial_summary=data.get('editorial_summary', ''),
        )
        return jsonify({"message": "Place saved successfully", "place_id": saved_place.id}), 201
    except Exception as e:
        return jsonify({"error": "Failed to save place"}), 500

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