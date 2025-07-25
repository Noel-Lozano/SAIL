from flask import render_template, request, redirect, session, flash, url_for, Flask
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required, JWTManager
from flask_sqlalchemy import SQLAlchemy
from app.backend.models.models import db, User, Search
from app.backend.models.db_utils import create_user, validate_user_login, save_search, get_user_searches, clear_user_searches
from datetime import timedelta
import os


app = Flask(__name__, template_folder='app/templates')
app.secret_key = os.getenv("SECRET_KEY") 

# Config
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///travelbot.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'your-secret-key'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=1)

db.init_app(app)
jwt = JWTManager(app)

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
        return redirect(url_for('login_page'))

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



# from weather_api import get_weather
# from genAI_api import generate_itinerary
# from db_utils import save_search, view_search_history, clear_search_history


# def make_itinerary():
#     """ Collects user input for itinerary generation and displays the result. """
#     city = input("Enter the city: ").strip()
#     date = input("Enter the date (YYYY-MM-DD): ").strip()
#     budget = input("Enter your budget: ").strip()
#     interests = input(
#         "Enter your interests (e.g., museums, food, hiking),or press Enter to skip: ").strip()

#     weather = get_weather(city, date)
#     itinerary = generate_itinerary(city, date, budget, weather, interests)

#     print("\nGenerated Itinerary:")
#     print(itinerary)
#     return city, date, budget, weather, itinerary


# def display_search_history():
#     """ Displays the search history from the database. """
#     print("\nSearch History:")
#     history = view_search_history()
#     if history.empty:
#         print("No search history found.")
#     else:
#         print(history)


# def clear_history():
#     """ Clears the search history after user confirmation. """
#     confirm = input(
#         "\nAre you sure you want to clear the search history? (yes/no): ")
#     confirm = confirm.strip().lower()
#     if confirm == 'yes':
#         clear_search_history()
#         print("Search history cleared.")
#     else:
#         print("Search history not cleared.")


# def saving_search(city, date, budget, weather, itinerary):
#     """ Saves the search entry to the database. """
#     print("\nSaving your search...")
#     entry = {
#         "city": city,
#         "date": date,
#         "budget": budget,
#         "weather": str(weather),
#         "itinerary": itinerary
#     }
#     save_search(entry)
#     print("Search saved successfully.")


# def main():
#     exit_program = False
#     print("\nWelcome to TravelBot, the Travel Itinerary Generator!")
#     print("You can generate personalized itineraries based on your preferences.")

#     while not exit_program:
#         print("\nMenu:")
#         print("1. Generate Itinerary")
#         print("2. View Search History")
#         print("3. Clear Search History")
#         print("4. Exit")

#         choice = input("\nPlease choose an option (1-4): ").strip()

#         if choice == '1':
#             city, date, budget, weather, itinerary = make_itinerary()
#             save_option = input(
#                 "Would you like to save this search? (yes/no): ").strip().lower()
#             if save_option == 'yes':
#                 saving_search(city, date, budget, weather, itinerary)
#             else:
#                 print("Search not saved.")
#         elif choice == '2':
#             view_search_history()
#         elif choice == '3':
#             clear_history()
#         elif choice == '4':
#             exit_program = True
#             print("Thank you for using TravelBot. Goodbye!")
#         else:
#             print("Invalid option. Please try again.")


# if __name__ == "__main__":
#     main()
