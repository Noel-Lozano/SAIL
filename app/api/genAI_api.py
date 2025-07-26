import os
import google.generativeai as genai
from datetime import datetime, timedelta
from itertools import permutations

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
        [4, 3]
    ]

    assert len(groupings) <= 10

    best_permutation = None
    best_max_avg_popularity = 100

    for permutation in permutations(groupings):
        for i in range(len(permutation)):
            date = start_date + timedelta(days=i)
            weekday = date.strftime("%A")
            weekday_number = (date.weekday() + 1) % 7

            all_open = True
            max_avg_popularity = 0

            for place_id in permutation[i]:
                place = all_places[place_id - 1]
                open24hours = place.open_hours == [] or place.open_hours == [{'open': {'day': 0, 'hour': 0, 'minute': 0}}]
                if not open24hours and not any(day['open']['day'] == weekday_number for day in place.open_hours):
                    all_open = False
                    break

                pop_data = next((p for p in place.popularity_data if p['name'] == weekday), None)
                if pop_data:
                    pop_data = [100 if x == 0 else x for x in pop_data['data']][9:]
                    print(pop_data, place.name)
                    max_avg_popularity = max(max_avg_popularity, sum(pop_data)/len(pop_data))

        print(permutation, max_avg_popularity, all_open)
        if all_open and max_avg_popularity < best_max_avg_popularity:
            best_max_avg_popularity = max_avg_popularity
            best_permutation = permutation
            print(f"[DEBUG] New best permutation found: {best_permutation} with max avg popularity {best_max_avg_popularity}")

    # return grouped_places
