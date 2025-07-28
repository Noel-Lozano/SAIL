from .models import db, User, Search, Place, Itinerary
from werkzeug.security import generate_password_hash, check_password_hash

def save_user_itinerary(user_id, name, itinerary):
    # if itinerary with name exists, update it
    existing_itinerary = Itinerary.query.filter_by(user_id=user_id, name=name).first()
    if existing_itinerary:
        existing_itinerary.itinerary = itinerary
        db.session.commit()
        return existing_itinerary

    itinerary = Itinerary(user_id=user_id, name=name, itinerary=itinerary)
    db.session.add(itinerary)
    db.session.commit()

def create_user(username, email, password):
    if get_user_by_email(email):
        return None
    
    hashed = generate_password_hash(password)
    user = User(username=username, email=email, hashed_password=hashed)
    db.session.add(user)
    db.session.commit()
    return user

def get_user_by_email(email):
    return User.query.filter_by(email=email).first()

def validate_user_login(email, password):
    user = get_user_by_email(email)
    if user and check_password_hash(user.hashed_password, password):
        return user
    return None

def save_search(user_id, data):
    search = Search(
        user_id=user_id,
        city=data['city'],
        date=data['date'],
        budget=data['budget'],
        weather=data.get('weather'),
        itinerary=data.get('itinerary')
    )
    db.session.add(search)
    db.session.commit()

def get_user_searches(user_id):
    return Search.query.filter_by(user_id=user_id).all()

def clear_user_searches(user_id):
    Search.query.filter_by(user_id=user_id).delete()
    db.session.commit()

def save_place(user_id, name, city, address, latitude, longitude, editorial_summary, popularity_data, open_hours):
    place = Place(
        user_id=user_id,
        name=name,
        city=city,
        address=address,
        latitude=latitude,
        longitude=longitude,
        editorial_summary=editorial_summary or "No summary provided",
        popularity_data=popularity_data,
        open_hours=open_hours or []
    )
    db.session.add(place)
    db.session.commit()
    return place

def get_user_places(user_id, city=None):
    """Get user's saved places with optional filters"""
    query = Place.query.filter_by(user_id=user_id)
    
    if city:
        query = query.filter(Place.city == city)

    return query.all()

def delete_place(place_id):
    """Delete a place by ID"""
    place = Place.query.get(place_id)
    if place:
        db.session.delete(place)
        db.session.commit()
        return True
    return False

def get_place_by_id(place_id, user_id=None):
    """Get a specific place by ID, optionally filtered by user"""
    query = Place.query.filter_by(id=place_id)
    if user_id:
        query = query.filter_by(user_id=user_id)
    return query.first()

def get_user_places_by_city(user_id):
    """Get user's places grouped by city"""
    places = Place.query.filter_by(user_id=user_id).order_by(Place.city).all()

    places_by_city = {}
    for place in places:
        if place.city not in places_by_city:
            places_by_city[place.city] = []
        places_by_city[place.city].append(place)
    
    return places_by_city

def get_user_stats(user_id):
    """Get statistics about user's saved places"""
    places = Place.query.filter_by(user_id=user_id).all()
    
    cities = set(place.city for place in places)
    
    return {
        'total_places': len(places),
        'unique_cities': len(cities),
        'cities': sorted(list(cities)),
    }