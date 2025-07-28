from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    hashed_password = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    searches = db.relationship('Search', backref='user', lazy=True)

class Search(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    date = db.Column(db.String(50), nullable=False)
    budget = db.Column(db.Float, nullable=False)
    weather = db.Column(db.Text)
    itinerary = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))

class Place(db.Model):
    id = db.Column(db.Integer, unique=True, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    editorial_summary = db.Column(db.Text)
    popularity_data = db.Column(db.JSON)
    open_hours = db.Column(db.JSON)

class Itinerary(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    itinerary = db.Column(db.JSON, nullable=False)
