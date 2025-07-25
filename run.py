from flask import render_template, request, redirect, session, flash, url_for, Flask
from flask_sqlalchemy import SQLAlchemy
from app.models.models import db, User, Search
from app.models.db_utils import create_user, validate_user_login, save_search, get_user_searches, clear_user_searches
from datetime import timedelta
import os

from app import create_app
app = create_app()

# Config
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///travelbot.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    db.create_all()

# ROUTES
@app.route('/')
def index():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        create_user(username, email, password)
        flash("User registered successfully!", "success")
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = validate_user_login(email, password)
        if user:
            session['user'] = user.username
            session['user_id'] = user.id
            flash(f"Welcome, {user.username}!", "success")
            return redirect(url_for('index'))
        else:
            flash("Invalid credentials", "danger")
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out.", "info")
    return redirect(url_for('login'))


@app.route('/search', methods=['POST'])
def search():
    if 'user_id' not in session:
        flash("You must be logged in to perform a search.", "danger")
        return redirect(url_for('login'))

    user_id = session['user_id']
    city = request.form['city']
    date = request.form['date']
    budget = float(request.form['budget'])
    weather = request.form.get('weather')
    itinerary = request.form.get('itinerary')

    data = {
        'city': city,
        'date': date,
        'budget': budget,
        'weather': weather,
        'itinerary': itinerary
    }

    save_search(user_id, data)
    flash("Search saved.", "success")
    return redirect(url_for('index'))


@app.route('/searches')
def get_searches():
    if 'user_id' not in session:
        flash("Please log in to view your searches.", "danger")
        return redirect(url_for('login'))

    user_id = session['user_id']
    searches = get_user_searches(user_id)
    return render_template('searches.html', searches=searches)


@app.route('/searches/clear', methods=['POST'])
def clear_searches():
    if 'user_id' not in session:
        flash("Please log in to clear your history.", "danger")
        return redirect(url_for('login'))

    user_id = session['user_id']
    clear_user_searches(user_id)
    flash("Search history cleared.", "info")
    return redirect(url_for('get_searches'))

if __name__ == '__main__':
    app.run(debug=True)
