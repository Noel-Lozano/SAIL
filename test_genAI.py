import unittest
from unittest.mock import patch, MagicMock
from genAI_api import generate_itinerary, build_prompt


class TestAIGenerator(unittest.TestCase):

    @patch("genAI_api.genai.GenerativeModel")
    def test_generate_itinerary_success(self, mock_model_class):
        """Test successful itinerary generation."""
        mock_model = MagicMock()
        mock_model.generate_content.return_value.text = "9am–11am: Visit the Louvre Museum"
        mock_model_class.return_value = mock_model

        result = generate_itinerary(
            destination="Paris",
            date="2025-08-15",
            budget="100",
            weather="sunny"
        )

        self.assertIn("Visit the Louvre", result)
        mock_model.generate_content.assert_called_once()
        print("test_generate_itinerary_success Passed")

    @patch("genAI_api.genai.GenerativeModel")
    def test_generate_itinerary_failure(self, mock_model_class):
        """Test itinerary generation failure due to API error."""
        mock_model = MagicMock()
        mock_model.generate_content.side_effect = Exception("API error")
        mock_model_class.return_value = mock_model

        result = generate_itinerary(
            destination="Paris",
            date="2025-08-15",
            budget="100",
            weather="sunny"
        )

        self.assertEqual(result, "Sorry, something went wrong while generating your itinerary.")
        print("test_generate_itinerary_failure Passed")

    def test_build_prompt(self):
        """Test building a prompt."""
        prompt = build_prompt("Rome", "2025-09-01", "75", "cloudy")
        self.assertIn("Rome", prompt)
        self.assertIn("2025-09-01", prompt)
        self.assertIn("cloudy", prompt)
        self.assertIn("75", prompt)
        self.assertNotIn("100", prompt)
        print("test_build_prompt Passed")


if __name__ == "__main__":
    unittest.main()
