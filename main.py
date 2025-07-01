from weather_api import get_weather
from genAI_api import generate_itinerary


def main():
    city = input("Enter the city: ").strip()
    date = input("Enter the date (YYYY-MM-DD): ").strip()
    budget = input("Enter your budget: ").strip()

    weather = get_weather(city, date)

    itinerary = generate_itinerary(city, date, budget, weather)
    print(itinerary)


if __name__ == "__main__":
    main()
