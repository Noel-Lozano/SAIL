import os
import google.generativeai as genai
from datetime import datetime

GEMINI_KEY = os.environ.get("GEMINI_KEY")
if not GEMINI_KEY:
    raise ValueError("GEMINI_KEY environment variable is not set.")

genai.configure(api_key=GEMINI_KEY)

def generate_groupings(all_places, start_date, end_date):
    """Generates groupings of places based on the provided date range."""
    start_date = datetime.strptime(start_date, "%Y-%m-%d")
    end_date = datetime.strptime(end_date, "%Y-%m-%d")
    num_days = (end_date - start_date).days + 1
    prompt = f"""
You are a smart travel planner. Group the following places into exactly {num_days} days of itinerary.

Consider location proximity and approximate visit duration (based on the editorial summary) to make the groupings balanced. Avoid placing too many high-effort or time-consuming places in a single day.

Each place is identified by an ID. Use only these IDs in your response. Ensure each ID is used only once.

You may explain your reasoning to help guide the grouping, although it's only for your use, so no need to over-explain.
Then begin your final output with "START" on a new line. After that, follow this exact format and include only the day numbers and place IDs:

Format:
Day 1: #, #, #
Day 2: #, #, #

Places:
"""

    for i, place in enumerate(all_places):
        prompt += f"\nID {i + 1}. {place.name} in {place.city} at {place.address} ({place.latitude}, {place.longitude})"
        prompt += f"\n   Editorial Summary: {place.editorial_summary}"

    # model = genai.GenerativeModel('gemma-3n-e4b-it')
    # response = model.generate_content(prompt)
    # print(f"[DEBUG] Generated groupings: {response.text}")
    
    # extract the groupings from the response
    # groupings = []
    # lines = response.text.lower().split("start")[1].strip().split("\n")
    # for line in lines:
    #     day, places = line.split(":")
    #     place_ids = [int(p) for p in places.split(",")]
    #     groupings.append(place_ids)

    groupings = [
        [1, 2],
        [3, 4]
    ]

    # determine if the groupings would benefit from the sun, and what the best temperature is
    prompt = f"""
You are a smart travel planner helping optimize a multi-day itinerary based on weather preferences.

Your task is to analyze the following list of daily activities and determine:
1. Whether each day would benefit from **sunny weather** ("yes" or "no")
2. The **ideal temperature** in Fahrenheit for that day’s activities, based on the type and location of places involved (use -1 if temperature isn’t important)

Guidelines:
- Consider the type of activity (e.g. outdoor vs. indoor) and its location.
- Outdoor activities often benefit from sun and may have temperature preferences (e.g., mild or warm).
- Indoor activities usually do not depend on sun or temperature.

**Only output the following format. Do not include any extra explanation or commentary:**
Day 1: yes/no, [temperature or -1]  
Day 2: yes/no, [temperature or -1]  

Example:
Day 1: yes, 75
Day 2: no, -1

Even if you include explanations, each answer line must be clearly formatted as shown.

Now evaluate the following days:
"""

    for i, day in enumerate(groupings):
        prompt += f"\nDay {i + 1}:\n"
        for place_id in day:
            place = all_places[place_id - 1]
            prompt += f"{place.name}: {place.editorial_summary}\n"
        
    # model = genai.GenerativeModel('gemma-3n-e4b-it')
    # response = model.generate_content(prompt)
    # print(f"[DEBUG] Generated groupings: {response.text}")

    # extract the weather preferences from the response
    # weather_prefs = []
    # lines = response.text.strip().split("\n")
    # for line in lines:
    #     if line.strip():
    #         day, prefs = line.split(":")
    #         sun, temp = prefs.strip().split(", ")
    #         weather_prefs.append({ "sunny_preferred": sun.lower().strip() == "yes", "temperature": int(temp.strip()) })
    weather_prefs = [
        {"sunny_preferred": True, "temperature": 75},
        {"sunny_preferred": False, "temperature": -1}
    ]

    return groupings, weather_prefs
