# Just a simple script to check registered users in the database
from app.models.models import db, User
from flask import Flask

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///travelbot.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    users = User.query.all()
    
    if not users:
        print("⚠️  No users found in the database.")
    else:
        print("✅ Registered users:")
        for user in users:
            print(f"- ID: {user.id} | Username: {user.username} | Email: {user.email} | Created: {user.created_at}")
