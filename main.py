from weather_api import get_weather

def main():
    city = input("Enter the city: ").strip()
    date = input("Enter the date (YYYY-MM-DD): ").strip()
    budget = input("Enter your budget: ").strip()

    weather = get_weather(city, date)
    