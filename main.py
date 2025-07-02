from weather_api import get_weather
from genAI_api import generate_itinerary
from db_utils import save_search, view_search_history, clear_search_history


def make_itinerary():
    """ Collects user input for itinerary generation and displays the result. """
    city = input("Enter the city: ").strip()
    date = input("Enter the date (YYYY-MM-DD): ").strip()
    budget = input("Enter your budget: ").strip()

    weather = get_weather(city, date)
    itinerary = generate_itinerary(city, date, budget, weather)

    print("\nGenerated Itinerary:")
    print(itinerary)
    return city, date, budget, weather, itinerary


def display_search_history():
    """ Displays the search history from the database. """
    print("\nSearch History:")
    history = view_search_history()
    if history.empty:
        print("No search history found.")
    else:
        print(history)


def clear_history():
    """ Clears the search history after user confirmation. """
    confirm = input(
        "\nAre you sure you want to clear the search history? (yes/no): ")
    confirm = confirm.strip().lower()
    if confirm == 'yes':
        clear_search_history()
        print("Search history cleared.")
    else:
        print("Search history not cleared.")


def saving_search(city, date, budget, weather, itinerary):
    """ Saves the search entry to the database. """
    print("\nSaving your search...")
    entry = {
        "city": city,
        "date": date,
        "budget": budget,
        "weather": str(weather),
        "itinerary": itinerary
    }
    save_search(entry)
    print("Search saved successfully.")


def main():
    exit_program = False
    print("\nWelcome to TravelBot, the Travel Itinerary Generator!")
    print("You can generate personalized itineraries based on your preferences.")

    while not exit_program:
        print("\nMenu:")
        print("1. Generate Itinerary")
        print("2. View Search History")
        print("3. Clear Search History")
        print("4. Exit")

        choice = input("\nPlease choose an option (1-4): ").strip()

        if choice == '1':
            city, date, budget, weather, itinerary = make_itinerary()
            save_option = input(
                "Would you like to save this search? (yes/no): ").strip().lower()
            if save_option == 'yes':
                saving_search(city, date, budget, weather, itinerary)
            else:
                print("Search not saved.")
        elif choice == '2':
            view_search_history()
        elif choice == '3':
            clear_history()
        elif choice == '4':
            exit_program = True
            print("Thank you for using TravelBot. Goodbye!")
        else:
            print("Invalid option. Please try again.")


if __name__ == "__main__":
    main()
