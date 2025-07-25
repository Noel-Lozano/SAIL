from .models import db, User, Search
from werkzeug.security import generate_password_hash, check_password_hash

def create_user(username, email, password):
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
