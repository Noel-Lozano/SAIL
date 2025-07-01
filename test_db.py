import unittest
import sqlalchemy as db
from db_utils import save_search, get_search_history, clear_search_history


class TestDatabaseUtils(unittest.TestCase):
    def setUp(self):
        """ Create a new in-memory SQLite database for each test. """
        self.engine = db.create_engine('sqlite:///:memory:')
        self.table_name = 'user_searches'

        with self.engine.connect() as conn:
            conn.execute(db.text(f"""
                CREATE TABLE {self.table_name} (
                    city TEXT,
                    date TEXT,
                    budget TEXT,
                    weather TEXT,
                    itinerary TEXT
                );
            """))

    def test_save_and_retrieve(self):
        """ Test saving a search entry to the database. """
        entry = {
            'city': 'Barcelona',
            'date': '2025-08-10',
            'budget': '1200',
            'weather': 'Sunny',
            'itinerary': 'Visit La Sagrada Familia'
        }

        save_search(entry, engine=self.engine)
        result = get_search_history(engine=self.engine)

        self.assertEqual(len(result), 1)
        self.assertEqual(result.iloc[0]['city'], "Barcelona")
        self.assertEqual(result.iloc[0]['date'], "2025-08-10")
        self.assertEqual(result.iloc[0]['budget'], "1200")
        self.assertIn('Sagrada Familia', result.iloc[0]['itinerary'])
        print("Save and retrieve test passed successfully.")

    def test_clear_search_history(self):
        """ Test clearing the search history. """
        entry1 = {
            'city': 'Madrid',
            'date': '2025-08-11',
            'budget': '1000',
            'weather': 'Cloudy',
            'itinerary': 'Visit Retiro Park'
        }
        entry2 = {
            'city': 'Seville',
            'date': '2025-08-12',
            'budget': '800',
            'weather': 'Rainy',
            'itinerary': 'Visit Alcazar'
        }

        save_search(entry1, engine=self.engine)
        save_search(entry2, engine=self.engine)
        self.assertEqual(len(get_search_history(engine=self.engine)), 2)

        clear_search_history(engine=self.engine)
        result = get_search_history(engine=self.engine)

        self.assertTrue(result.empty)
        print("Clear search history test passed successfully.")


if __name__ == '__main__':
    unittest.main()
