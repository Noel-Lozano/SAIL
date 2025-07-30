import unittest
from app import create_app
from app.models.models import db, User, Itinerary, Search, Place
from app.models.db_utils import (
    create_user, validate_user_login, save_user_itinerary, save_search,
    get_user_searches, clear_user_searches, save_place, get_user_places,
    delete_place, get_place_by_id
)

class TestAppDatabase(unittest.TestCase):

    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

        with self.app.app_context():
            db.init_app(self.app)
            db.create_all()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_create_user_success(self):
        with self.app.app_context():
            user = create_user("alice", "alice@example.com", "password")
            self.assertIsNotNone(user)

    def test_create_user_duplicate_email(self):
        with self.app.app_context():
            create_user("alice", "alice@example.com", "password")
            user2 = create_user("bob", "alice@example.com", "otherpass")
            self.assertIsNone(user2)

    def test_validate_user_login_success(self):
        with self.app.app_context():
            create_user("alice", "alice@example.com", "password")
            user = validate_user_login("alice@example.com", "password")
            self.assertIsNotNone(user)

    def test_validate_user_login_failure(self):
        with self.app.app_context():
            create_user("alice", "alice@example.com", "password")
            user = validate_user_login("alice@example.com", "wrongpassword")
            self.assertIsNone(user)

    def test_save_user_itinerary_create(self):
        with self.app.app_context():
            user = create_user("alice", "alice@example.com", "password")
            save_user_itinerary(user.id, "NYC Trip", "3-day itinerary")
            itinerary = Itinerary.query.filter_by(user_id=user.id).first()
            self.assertIsNotNone(itinerary)
            self.assertEqual(itinerary.name, "NYC Trip")

    def test_save_user_itinerary_update(self):
        with self.app.app_context():
            user = create_user("alice", "alice@example.com", "password")
            save_user_itinerary(user.id, "Trip", "v1")
            save_user_itinerary(user.id, "Trip", "v2")
            itinerary = Itinerary.query.filter_by(user_id=user.id).first()
            self.assertEqual(itinerary.itinerary, "v2")

    def test_save_and_get_user_search(self):
        with self.app.app_context():
            user = create_user("alice", "alice@example.com", "password")
            save_search(user.id, {
                "city": "Paris", "date": "2025-08-01",
                "budget": "500", "weather": "Sunny", "itinerary": "Eiffel Tower"
            })
            searches = get_user_searches(user.id)
            self.assertEqual(len(searches), 1)
            self.assertEqual(searches[0].city, "Paris")

    def test_clear_user_searches(self):
        with self.app.app_context():
            user = create_user("alice", "alice@example.com", "password")
            save_search(user.id, {
                "city": "Paris", "date": "2025-08-01",
                "budget": "500", "weather": "Sunny", "itinerary": "Eiffel Tower"
            })
            clear_user_searches(user.id)
            searches = get_user_searches(user.id)
            self.assertEqual(len(searches), 0)

    def test_save_and_get_place(self):
        with self.app.app_context():
            user = create_user("alice", "alice@example.com", "password")
            save_place(user.id, "Louvre", "Paris", "Rue", 48.86, 2.34, "Famous", "High", [])
            places = get_user_places(user.id)
            self.assertEqual(len(places), 1)
            self.assertEqual(places[0].name, "Louvre")

    def test_delete_place(self):
        with self.app.app_context():
            user = create_user("alice", "alice@example.com", "password")
            place = save_place(user.id, "Louvre", "Paris", "Rue", 48.86, 2.34, "Famous", "High", [])
            success = delete_place(place.id)
            self.assertTrue(success)
            self.assertIsNone(get_place_by_id(place.id))


if __name__ == "__main__":
    unittest.main()
