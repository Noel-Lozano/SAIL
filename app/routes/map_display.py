import os
from flask import render_template, request, Blueprint, jsonify, session
from numpy import place
from app.api.map_api import get_places_from_city, get_popularity
from app.api.genAI_api import generate_groupings, recommend_places_with_interests
from app.api.weather_api import get_weather
from app.models.db_utils import save_place, get_user_places, delete_place, save_user_itinerary
from app.models.models import Place, Itinerary, User
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
    user = User.query.get(user_id)

    city = request.args.get('city', 'New York')
    place = request.args.get('place', '')
    page_n = request.args.get('page', 1, type=int)
    places = get_places_from_city(city, place, page_n) or []

    user_interests = user.interests if user and user.ai_enabled else None
    ai_recommendations = None
    if user and user.ai_enabled and user_interests:
        ai_recommendations = recommend_places_with_interests(city, user_interests)

    return render_template("planning.html", 
                           places=places, 
                           google_maps_api_key=FRONTEND_MAP_API,
                           city=city, 
                           place=place, 
                           user_places=user_places,
                           total_places=len(user_places),
                           user_interests=user_interests,
                           ai_recommendations=ai_recommendations)

def optimize_groupings(all_places, groupings, weather_prefs, weather_data, start_date):
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

                # Use a local variable for open_hours
                open_hours = place.get("open_hours") if isinstance(place, dict) else place.open_hours

                # Ensure it's a list
                if not isinstance(open_hours, list):
                    try:
                        open_hours = json.loads(open_hours) if open_hours else []
                    except:
                        open_hours = []

                # Assume always open if still empty
                if not open_hours:
                    open_hours = [{"open": {"day": d, "hour": 0, "minute": 0}} for d in range(7)]

                # Check if the place is open on the current day
                open24hours = open_hours == [] or open_hours == [{'open': {'day': 0, 'hour': 0, 'minute': 0}}]
                if open24hours or any(
                    isinstance(day, dict) and 'open' in day and day['open'].get('day') == weekday_number
                    for day in open_hours
                ):
                    open_percentage += 100 / tot_count

                # Check popularity data
                pop_data = next((p for p in place["popularity_data"] if p['name'] == weekday), None) if isinstance(place, dict) else next((p for p in place.popularity_data if p['name'] == weekday), None)
                if pop_data:
                    pop_data = [100 if x == 0 else x for x in pop_data['data']][9:]
                    max_avg_popularity = max(max_avg_popularity, sum(pop_data) / len(pop_data))

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
        temperature_diff = (temperature_diff / (60 * temperature_days)) * 100 if temperature_days > 0 else 0

        open_scale, pop_scale, cloudy_scale, temp_scale = 10, -3, -3, -2
        score = (open_percentage * open_scale) + (max_avg_popularity * pop_scale) + (cloudy_percentage * cloudy_scale) + (temperature_diff * temp_scale)
        if score > best_score:
            best_score = score
            best_permutation = permutation
        
    best_permutation = [places for places, _ in best_permutation]
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

        # Check if user has any places saved
        if not all_places:
            dict_places = []
            itinerary = [{"date": "Unassigned", "places": []}]
        else:
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
                    if i < len(weather_data):
                        itinerary[-1]['weather'] = weather_data[i]

                if unused_places:
                    unused_places_list = [dict_places[place_id - 1] for place_id in unused_places]
                    itinerary.append({
                        "date": "Unassigned",
                        "places": unused_places_list
                    })
            else:
                itinerary = [{"date": "Unassigned", "places": dict_places}]

        for i, day in enumerate(itinerary):
            day['color'] = get_random_bold_color()
            for place in day['places']:
                place['color'] = day['color']
                place['date'] = day['date'].split(",")[0]
    
    saved_itineraries = [it.name for it in Itinerary.query.filter_by(user_id=user_id).all()]
    print(f"[DEBUG] Saved itineraries: {saved_itineraries}")

    return render_template("build_itinerary.html",
                         itinerary=itinerary,
                         all_places=dict_places,
                         start_date=start_date.strftime("%Y-%m-%d") if isinstance(start_date, datetime) else start_date,
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

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return render_template("cart_partial.html", user_places=all_places, total_places=len(all_places))

    return render_template("cart.html", user_places=all_places, total_places=len(all_places))


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

    # Normalize open_hours into a Python list
    open_hours = data.get('open_hours', [])
    if isinstance(open_hours, str):
        try:
            open_hours = json.loads(open_hours) if open_hours.strip() else []
        except Exception:
            open_hours = []
    if not isinstance(open_hours, list):
        open_hours = []

    # Initialize variables
    popularity_data = []
    place_id = data.get('id') or data.get('place_id')

    # Handle AI-recommended places (they don't have Google place_id initially)
    if not place_id:
        print(f"[DEBUG] AI recommendation detected: {data.get('name')} in {data.get('city')}")
        # Search for the place using Google Places API
        google_results = get_places_from_city(data['city'], data['name'], page_n=1)
        
        if google_results:
            # Use the improved matching function
            best_match = find_best_match(data['name'], google_results)
            print(f"[DEBUG] Best match found: {best_match['name']} (original: {data['name']})")
            
            # Update data with Google Places information
            data.update({
                "name": best_match['name'],
                "address": best_match['address'],
                "latitude": best_match["location"]["lat"],
                "longitude": best_match["location"]["lng"],
                "editorial_summary": best_match.get('editorial_summary', data.get('editorial_summary', '')),
                "open_hours": best_match.get('open_hours', []),
                "place_id": best_match['place_id'],
            })
            
            place_id = best_match['place_id']
            open_hours = best_match.get('open_hours', [])
            
            print(f"[DEBUG] Updated AI recommendation with Google data: {data['name']}")
        else:
            print(f"[DEBUG] No Google results found for AI recommendation: {data['name']}")
            # Keep original AI recommendation data if no Google match found

    # Get popularity data if we have a place_id
    if place_id:
        print(f"[DEBUG] Fetching popularity data for place_id: {place_id}")
        try:
            popularity_data = get_popularity(place_id)
        except Exception as e:
            print(f"[DEBUG] Failed to get popularity data: {e}")
            popularity_data = []

    # Check if place already exists for this user
    # Use more flexible matching for coordinates (round to avoid floating point precision issues)
    existing_place = Place.query.filter_by(
        user_id=user_id,
        name=data['name'],
        city=data['city']
    ).filter(
        Place.latitude.between(data['latitude'] - 0.001, data['latitude'] + 0.001),
        Place.longitude.between(data['longitude'] - 0.001, data['longitude'] + 0.001)
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
            popularity_data=popularity_data,
            open_hours=open_hours
        )
        return jsonify({"message": "Place saved successfully", "place_id": saved_place.id}), 201
    except Exception as e:
        print(f"[DEBUG] Error saving place: {e}")
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
    
# helper function for better place matching

def find_best_match(ai_place_name, google_results):
    """
    Find the best matching Google place for an AI recommendation
    """
    if not google_results:
        return None
    
    ai_name_lower = ai_place_name.lower().strip()
    
    # First, try exact match
    for result in google_results:
        if result['name'].lower().strip() == ai_name_lower:
            return result
    
    # Then try partial matches
    for result in google_results:
        result_name_lower = result['name'].lower().strip()
        # Check if AI name is contained in result name or vice versa
        if ai_name_lower in result_name_lower or result_name_lower in ai_name_lower:
            return result
    
    # Finally, try word-based matching
    ai_words = set(ai_name_lower.split())
    best_match = None
    best_score = 0
    
    for result in google_results:
        result_words = set(result['name'].lower().strip().split())
        # Calculate Jaccard similarity
        intersection = ai_words.intersection(result_words)
        union = ai_words.union(result_words)
        
        if len(union) > 0:
            score = len(intersection) / len(union)
            if score > best_score and score > 0.3:  # Minimum similarity threshold
                best_score = score
                best_match = result
    
    # If we found a good match, return it; otherwise return the first result
    return best_match if best_match else google_results[0]

# debugging route to help troubleshoot
@map_display_bp.route("/debug_ai_place", methods=['POST'])
def debug_ai_place():
    """Debug endpoint to check AI place matching"""
    if 'user_id' not in session:
        return jsonify({"error": "Not logged in"}), 401
    
    data = request.get_json()
    place_name = data.get('name')
    city = data.get('city')
    
    if not place_name or not city:
        return jsonify({"error": "Missing name or city"}), 400
    
    # Search for the place
    google_results = get_places_from_city(city, place_name, page_n=1)
    
    debug_info = {
        "ai_place_name": place_name,
        "city": city,
        "google_results_count": len(google_results) if google_results else 0,
        "google_results": [
            {
                "name": r['name'],
                "address": r['address'],
                "place_id": r['place_id']
            } for r in (google_results[:3] if google_results else [])
        ]
    }
    
    if google_results:
        best_match = find_best_match(place_name, google_results)
        debug_info["best_match"] = {
            "name": best_match['name'],
            "address": best_match['address'],
            "place_id": best_match['place_id']
        }
    
    return jsonify(debug_info)