from unittest.mock import patch
from weather_api import get_weather
from genAI_api import build_prompt, generate_itinerary
from db_utils import (
    save_search,
    get_search_history,
    clear_search_history,
)


@patch("weather_api.requests.get")
def test_get_weather_success(mock_get):
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {
        "list": [
            {
                "dt_txt": "2025-07-03 15:00:00",
                "main": {"temp": 24},
                "weather": [{"description": "clear sky"}]
            }
        ]
    }

    result = get_weather("London", "2025-07-03")
    assert result == {"temperature": 24, "description": "clear sky"}


def test_build_prompt_contains_all_inputs():
    prompt = build_prompt("Tokyo", "2025-07-05", 150, "sunny and warm", "museums")
    assert "Tokyo" in prompt
    assert "2025-07-05" in prompt
    assert "150" in prompt
    assert "sunny and warm" in prompt
    assert "museums" in prompt


@patch("genAI_api.genai.GenerativeModel.generate_content")
def test_generate_itinerary_returns_string(mock_generate):
    mock_generate.return_value.text = "Your itinerary for Tokyo..."
    response = generate_itinerary("Tokyo", "2025-07-05", 150, "sunny", "museums")
    assert isinstance(response, str)
    assert "Tokyo" in response or "itinerary" in response


def test_save_and_fetch_search():
    clear_search_history()
    entry = {
        "city": "Paris",
        "date": "2025-07-01",
        "budget": "100",
        "weather": "{'temperature': 25, 'description': 'clear'}",
        "itinerary": "Visit the Eiffel Tower in the morning."
    }
    save_search(entry)
    history = get_search_history()
    assert not history.empty
    assert "Paris" in history["city"].values
