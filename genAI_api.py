import os
import google.generativeai as genai

GEMINI_KEY = os.environ.get("GEMINI_KEY")
if not GEMINI_KEY:
    raise ValueError("GEMINI_KEY environment variable is not set.")

genai.configure(api_key=GEMINI_KEY)


def build_prompt(destination, date, budget, weather):
    """Builds a prompt for the Gemini model based on user input."""
    prompt = f"""
        You are a smart travel planner.
        Create a personalized day itinerary for a user visiting {destination} on {date}.
        The weather is expected to be {weather}.
        The budget for the day is {budget} (in USD).

        Give me a schedule with time blocks (e.g., 9am–11am), and briefly describe each activity.
        Ensure it fits the weather and budget.
        Return the plan in a clean, readable format.
    """
    return prompt.strip()


def generate_itinerary(destination, date, budget, weather):
    """Generates a travel itinerary using the Gemini model."""
    prompt = build_prompt(destination, date, budget, weather)

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        return response.text
    # except Exception as e:
        # print(f"[ERROR] Failed to generate itinerary: {e}")
    except Exception:
        return "Sorry, something went wrong while generating your itinerary."
