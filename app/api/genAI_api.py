import os
import google.generativeai as genai
from datetime import datetime
import json
import re

GEMINI_KEY = os.environ.get("GEMINI_KEY")
if not GEMINI_KEY:
    raise ValueError("GEMINI_KEY environment variable is not set.")

genai.configure(api_key=GEMINI_KEY)

def generate_groupings(all_places, start_date, end_date):
    """Generates groupings of places based on the provided date range."""
    if not all_places:
        return [], []
    
    start_date = datetime.strptime(start_date, "%Y-%m-%d")
    end_date = datetime.strptime(end_date, "%Y-%m-%d")
    num_days = (end_date - start_date).days + 1
    
    prompt = f"""
You are a smart travel planner. Group the following {len(all_places)} places into exactly {num_days} days of itinerary.

Consider location proximity and approximate visit duration (based on the editorial summary) to make the groupings balanced. Avoid placing too many high-effort or time-consuming places in a single day.

Each place is identified by an ID from 1 to {len(all_places)}. Use only these IDs in your response. IMPORTANT: Ensure each ID is used AT MOST once and only use IDs that exist (1 to {len(all_places)})!

You may explain your reasoning to help guide the grouping, although it's only for your use, so no need to over-explain.
Then begin your final output with "$$$" on a new line. After that, follow this exact format and include only the day numbers and place IDs:
Day 1: #, #, ...
Day 2: #, #, ...

Ensure each ID is used AT MOST once and only use valid IDs (1-{len(all_places)})!
Places:
"""

    for i, place in enumerate(all_places):
        prompt += f"\nID {i + 1}. {place.name} in {place.city} at {place.address} ({place.latitude}, {place.longitude})"
        prompt += f"\n   Editorial Summary: {place.editorial_summary or 'No description available'}"

    model = genai.GenerativeModel('gemini-2.0-flash-lite')
    response = model.generate_content(prompt)
    print(f"[DEBUG] Generated groupings: {response.text}")
    
    # extract the groupings from the response
    groupings = []
    try:
        lines = response.text.lower().split("$$$")[1].strip().split("\n")
        for line in lines:
            if ":" in line:
                day, places = line.split(":", 1)  # Split only on first colon
                if places.strip():
                    # Extract numbers and filter out invalid IDs
                    place_ids = []
                    for place_str in places.split(","):
                        try:
                            place_id = int(place_str.strip())
                            # Only include valid IDs within range
                            if 1 <= place_id <= len(all_places):
                                place_ids.append(place_id)
                        except ValueError:
                            continue
                    # Remove duplicates while preserving order
                    place_ids = list(dict.fromkeys(place_ids))
                    groupings.append(place_ids)
                else:
                    groupings.append([])
    except (IndexError, ValueError) as e:
        print(f"[ERROR] Failed to parse groupings: {e}")
        # Fallback: distribute places evenly across days
        places_per_day = len(all_places) // num_days
        remainder = len(all_places) % num_days
        
        current_place = 1
        for day in range(num_days):
            day_places = []
            places_for_this_day = places_per_day + (1 if day < remainder else 0)
            for _ in range(places_for_this_day):
                if current_place <= len(all_places):
                    day_places.append(current_place)
                    current_place += 1
            groupings.append(day_places)

    # Ensure we have the right number of days
    while len(groupings) < num_days:
        groupings.append([])
    
    # Truncate if we have too many days
    groupings = groupings[:num_days]

    # determine if the groupings would benefit from the sun, and what the best temperature is
    prompt = f"""
You are a smart travel planner helping optimize a multi-day itinerary based on weather preferences.

Your task is to analyze the following list of daily activities and determine:
1. Whether each day would benefit from **sunny weather** ("yes" or "no")
2. The **ideal temperature** in Fahrenheit for that day's activities, based on the type and location of places involved (use -1 if temperature isn't important)

Guidelines:
- Consider the type of activity (e.g. outdoor vs. indoor) and its location.
- Outdoor activities often benefit from sun and may have temperature preferences (e.g., mild or warm).
- If any place in a day would benefit from sun, mark the entire day as "yes" for sun. Similarly, if any place has a temperature preference, use that temperature for the day.

**Only output the following format. Do not include any extra explanation or commentary:**
Day 1: yes/no, [temperature or -1]  
Day 2: yes/no, [temperature or -1]  

Example:
Day 1: yes, 75
Day 2: no, -1

No other text should be included in your response.
Now evaluate the following days:
"""

    for i, day in enumerate(groupings):
        prompt += f"\nDay {i + 1}:\n"
        if not day:  # Handle empty days
            prompt += "No places assigned\n"
        else:
            for place_id in day:
                if 1 <= place_id <= len(all_places):  # Additional safety check
                    place = all_places[place_id - 1]
                    prompt += f"{place.name}: {place.editorial_summary or 'No description available'}\n"

    model = genai.GenerativeModel('gemini-2.0-flash-lite')
    response = model.generate_content(prompt)
    print(f"[DEBUG] Weather preferences: {response.text}")

    # extract the weather preferences from the response
    weather_prefs = []
    try:
        lines = response.text.strip().split("\n")
        for line in lines:
            if line.strip() and ":" in line:
                day, prefs = line.split(":", 1)
                if "," in prefs:
                    sun, temp = prefs.strip().split(",", 1)
                    try:
                        temp_val = int(temp.strip())
                    except ValueError:
                        temp_val = -1
                    weather_prefs.append({
                        "sunny_preferred": sun.lower().strip() == "yes", 
                        "temperature": temp_val
                    })
                else:
                    # Fallback if format is wrong
                    weather_prefs.append({
                        "sunny_preferred": False, 
                        "temperature": -1
                    })
    except Exception as e:
        print(f"[ERROR] Failed to parse weather preferences: {e}")
        # Fallback weather preferences
        for _ in range(num_days):
            weather_prefs.append({
                "sunny_preferred": False, 
                "temperature": -1
            })

    # Ensure we have weather preferences for all days
    while len(weather_prefs) < num_days:
        weather_prefs.append({"sunny_preferred": False, "temperature": -1})
    
    weather_prefs = weather_prefs[:num_days]

    return groupings, weather_prefs

def extract_json_from_text(text):
    """Extract JSON from text that might contain other content."""
    # Try to find JSON array in the text
    json_pattern = r'\[[\s\S]*?\]'
    matches = re.findall(json_pattern, text)
    
    for match in matches:
        try:
            return json.loads(match)
        except json.JSONDecodeError:
            continue
    
    # If no valid JSON array found, try to find JSON objects
    json_obj_pattern = r'\{[\s\S]*?\}'
    matches = re.findall(json_obj_pattern, text)
    
    valid_objects = []
    for match in matches:
        try:
            obj = json.loads(match)
            if isinstance(obj, dict) and 'name' in obj:
                valid_objects.append(obj)
        except json.JSONDecodeError:
            continue
    
    return valid_objects if valid_objects else []

def recommend_places_with_interests(city, interests):
    """Generates a list of recommended places based on user interests."""
    prompt = f"""
You are a smart travel planner. Recommend exactly 3-5 places in {city} based on the user's interests:
{interests or "No specific interests provided."}

For each place, provide:
- Name (real place name)
- Short description (1-2 sentences)
- Why it matches the interests (1 sentence)
- Accurate latitude and longitude coordinates (decimal format)
- Open hours: an array of objects like this:
      [
        {{"open": {{"day": 1, "hour": 9, "minute": 0}}}},
        {{"open": {{"day": 1, "hour": 17, "minute": 0}}}}
      ]
      Days are 0=Sunday through 6=Saturday. Use empty list [] if unknown.

IMPORTANT: Return ONLY a valid JSON array. No other text before or after the JSON.

Format:
[
    {{
        "name": "Actual Place Name",
        "description": "Brief description of what this place offers",
        "reason": "How this place matches the user's interests",
        "latitude": 40.7589,
        "longitude": -73.9851
        "open_hours": [
            {{"open": {{"day": 1, "hour": 9, "minute": 0}}}},
            {{"open": {{"day": 1, "hour": 17, "minute": 0}}}}
        ]
    }}
]

Ensure coordinates are accurate for {city} and the places actually exist.
"""
    
    model = genai.GenerativeModel('gemini-2.0-flash-lite')
    response = model.generate_content(prompt)
    
    raw_text = response.text.strip()
    match = re.search(r'\[.*\]', raw_text, re.DOTALL)
    if not match:
        print("[ERROR] Gemini did not return JSON.")
        return []
    json_text = match.group(0)

    # Try parsing the JSON
    try:
        recommendations = json.loads(json_text)
        # Ensure open_hours is always a list
        for rec in recommendations:
            if "open_hours" not in rec or not isinstance(rec["open_hours"], list):
                rec["open_hours"] = []
        return recommendations
    except json.JSONDecodeError as e:
        print(f"[ERROR] Failed to parse JSON: {e}")
        return []