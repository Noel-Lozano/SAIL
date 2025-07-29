import os
from flask import render_template, request, Blueprint, jsonify, session
from numpy import place
from app.api.map_api import get_places_from_city, get_popularity
from app.api.genAI_api import generate_groupings
from app.api.weather_api import get_weather
from app.models.db_utils import save_place, get_user_places, delete_place, save_user_itinerary
from app.models.models import Place, Itinerary
from datetime import datetime, timedelta
from itertools import permutations
import json
import random
import colorsys

def get_random_bold_color():
    hues = [0, 30, 60, 120, 180, 210, 270, 300]
    h = random.choice(hues) / 360.0
    s = 1.0
    l = random.uniform(0.4, 0.5)

    r, g, b = colorsys.hls_to_rgb(h, l, s)
    r, g, b = int(r * 255), int(g * 255), int(b * 255)

    return f'rgb({r}, {g}, {b})'

map_display_bp = Blueprint('map_display', __name__)

FRONTEND_MAP_API = os.getenv("FRONTEND_MAP_API")

@map_display_bp.route("/planning")
def planning():
    if 'user_id' not in session:
        return render_template("login.html", message="Please log in to view your itinerary")

    user_id = session['user_id']
    user_places = get_user_places(user_id=user_id)

    city = request.args.get('city', 'New York')
    place = request.args.get('place', '')
    page_n = request.args.get('page', 1, type=int)
    places = get_places_from_city(city, place, page_n) or []

    return render_template("planning.html", 
                           places=places, 
                           google_maps_api_key=FRONTEND_MAP_API,
                           city=city, 
                           place=place, 
                           user_places=user_places,
                           total_places=len(user_places))

def optimize_groupings(all_places, groupings, weather_prefs, weather_data, start_date):
    # pair each grouping with its weather preference
    tot_count = sum(len(day) for day in groupings)
    groupings = [(grouping, weather_prefs[i]) for i, grouping in enumerate(groupings)]

    best_permutation = None
    best_score = -float('inf')

    for permutation in permutations(groupings):
        open_percentage = 0

        max_avg_popularity = 0

        cloudy_percentage = 0
        cloudy_days = 0

        temperature_diff = 0
        temperature_days = 0


        for i, (places, weather_pref) in enumerate(permutation):
            date = start_date + timedelta(days=i)
            weekday = date.strftime("%A")
            weekday_number = (date.weekday() + 1) % 7

            for place_id in places:
                place = all_places[place_id - 1]

                # Check if the place is open on the current day
                open24hours = place.open_hours == [] or place.open_hours == [{'open': {'day': 0, 'hour': 0, 'minute': 0}}]
                if open24hours or any(day['open']['day'] == weekday_number for day in place.open_hours):
                    open_percentage += 100/tot_count

                # Check popularity data
                pop_data = next((p for p in place.popularity_data if p['name'] == weekday), None)
                if pop_data:
                    pop_data = [100 if x == 0 else x for x in pop_data['data']][9:]
                    max_avg_popularity = max(max_avg_popularity, sum(pop_data)/len(pop_data))

            # Check cloudy weather preference
            if weather_pref['sunny_preferred']:
                cloudy_percentage += weather_data[i]['avg_cloud']
                cloudy_days += 1

            # Check temperature preference
            if weather_pref['temperature'] != -1:
                avg_fahrenheit = weather_data[i]['avg_temp'] * 9/5 + 32
                temperature_diff += abs(avg_fahrenheit - weather_pref['temperature'])
                temperature_days += 1

        cloudy_percentage = cloudy_percentage / cloudy_days if cloudy_days > 0 else 0
        # Scale temperature diff as percent of max possible diff (60 degrees)
        temperature_diff = (temperature_diff / (60 * temperature_days)) * 100 if temperature_days > 0 else 0

        open_scale, pop_scale, cloudy_scale, temp_scale = 10, -3, -3, -2
        score = (open_percentage * open_scale) + (max_avg_popularity * pop_scale) + (cloudy_percentage * cloudy_scale) + (temperature_diff * temp_scale)
        print(f"[DEBUG] Permutation score: {score} (Open: {open_percentage}, Pop: {max_avg_popularity}, Cloudy: {cloudy_percentage}, Temp Diff: {temperature_diff})")
        if score > best_score:
            best_score = score
            best_permutation = permutation
        
    best_permutation = [places for places, _ in best_permutation]
    print(f"[DEBUG] Best permutation score: {best_score}")
    print(f"[DEBUG] Best permutation: {best_permutation}")
    return best_permutation

@map_display_bp.route("/itinerary")
def itinerary():
    if 'user_id' not in session:
        return render_template("login.html", message="Please log in to view your itinerary")
    
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    itinerary_name = request.args.get('name')

    if itinerary_name:
        user_id = session['user_id']
        itinerary = Itinerary.query.filter_by(user_id=user_id, name=itinerary_name).first()
        itinerary = itinerary.itinerary if itinerary else []
        dict_places = sum([day['places'] for day in itinerary], [])

    else:
        user_id = session['user_id']
        all_places = get_user_places(user_id=user_id)

        dict_places = [place.__dict__ for place in all_places]
        for place in dict_places: place.pop('_sa_instance_state')

        itinerary = []
        if start_date and end_date:
            groupings, weather_prefs = generate_groupings(all_places, start_date, end_date)
            weather_data = get_weather(all_places[0].city, start_date, end_date)
            start_date = datetime.strptime(start_date, "%Y-%m-%d")
            best_permutation = optimize_groupings(all_places, groupings, weather_prefs, weather_data, start_date)

            unused_places = set(range(1, len(all_places) + 1)) - {place_id for day in best_permutation for place_id in day}
            for i, day in enumerate(best_permutation):
                date = start_date + timedelta(days=i)
                itinerary.append({
                    "date": date.strftime("%A, %B %d").replace(" 0", " "),
                    "places": [dict_places[place_id - 1] for place_id in day]
                })

            if unused_places:
                unused_places_list = [dict_places[place_id - 1] for place_id in unused_places]
                itinerary.append({
                    "date": "Unassigned",
                    "places": unused_places_list
                })
        else:
            itinerary = [{"date": "Unassigned", "places": dict_places}]

        for day in itinerary:
            day['color'] = get_random_bold_color()
            for place in day['places']:
                place['color'] = day['color']
                place['date'] = day['date'].split(",")[0]
    
    saved_itineraries = [it.name for it in Itinerary.query.filter_by(user_id=user_id).all()]
    print(f"[DEBUG] Saved itineraries: {saved_itineraries}")

    return render_template("build_itinerary.html",
                         itinerary=itinerary,
                         all_places=dict_places,
                         start_date=start_date.strftime("%Y-%m-%d") if start_date else None,
                         end_date=end_date,
                         saved_itineraries=saved_itineraries,
                         itinerary_name=itinerary_name,
                         google_maps_api_key=FRONTEND_MAP_API)

@map_display_bp.route("/cart")
def cart():
    if 'user_id' not in session:
        return render_template("login.html", message="Please log in to view your cart")

    user_id = session['user_id']
    all_places = get_user_places(user_id=user_id)

    return render_template("cart.html",
                         user_places=all_places,
                         total_places=len(all_places))

@map_display_bp.route("/save_itinerary", methods=['POST'])
def save_itinerary():
    if 'user_id' not in session:
        return jsonify({"error": "Please log in to save itineraries"}), 401

    user_id = session['user_id']
    data = request.get_json()

    itinerary_name = data.get('name')
    itinerary_data = data.get('itinerary')

    if not itinerary_name or not itinerary_data:
        return jsonify({"error": "Invalid itinerary data"}), 400

    try:
        # Save the itinerary to the database
        save_user_itinerary(user_id=user_id, name=itinerary_name, itinerary=itinerary_data)
        return jsonify({"success": True}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

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

    place_id = data.get('id', None)
    if place_id:
        print("DEBUG: Fetching popularity data for place_id:", place_id)
        popularity_data = get_popularity(place_id)
    else:
        popularity_data = []

    try:
        saved_place = save_place(
            user_id=user_id,
            name=data['name'],
            city=data['city'],
            address=data['address'],
            latitude=data['latitude'],
            longitude=data['longitude'],
            editorial_summary=data.get('editorial_summary', ''),
            popularity_data=popularity_data,
            open_hours=data.get('open_hours', '[]')
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