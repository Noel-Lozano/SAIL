from .models import db, User, Search, Place
from werkzeug.security import generate_password_hash, check_password_hash

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
    return Search.query.filter_by(user_id=user_id).order_by(Search.created_at.desc()).all()

def clear_user_searches(user_id):
    Search.query.filter_by(user_id=user_id).delete()
    db.session.commit()

def save_place(user_id, name, city, country, address, latitude, longitude):
    place = Place(
        user_id=user_id,
        name=name,
        city=city,
        country=country,
        address=address,
        latitude=latitude,
        longitude=longitude
    )
    db.session.add(place)
    db.session.commit()
    return place

def get_user_places(user_id, city=None, country=None, date_from=None, date_to=None):
    """Get user's saved places with optional filters"""
    query = Place.query.filter_by(user_id=user_id)
    
    if city:
        query = query.filter(Place.city == city)
    
    if country:
        query = query.filter(Place.country == country)
    
    if date_from:
        query = query.filter(Place.created_at >= date_from)
    
    if date_to:
        query = query.filter(Place.created_at <= date_to)
    
    return query.order_by(Place.created_at.desc()).all()

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
    places = Place.query.filter_by(user_id=user_id).order_by(Place.city, Place.created_at.desc()).all()
    
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
    countries = set(place.country for place in places if place.country)
    
    return {
        'total_places': len(places),
        'unique_cities': len(cities),
        'unique_countries': len(countries),
        'cities': sorted(list(cities)),
        'countries': sorted(list(countries))
    }