import pandas as pd
import sqlalchemy as db

DB_NAME = 'search_history.db'
TABLE_NAME = 'user_searches'
DEFAULT_ENGINE = db.create_engine(f'sqlite:///{DB_NAME}')


def save_search(entry_dict, engine=DEFAULT_ENGINE):
    """Takes a dictionary with search data and appends it to the database."""
    df = pd.DataFrame([entry_dict])
    df.to_sql(TABLE_NAME, con=engine, if_exists='append', index=False)


def get_search_history(engine=DEFAULT_ENGINE):
    """Returns all saved searches as a DataFrame."""
    with engine.connect() as conn:
        result = conn.execute(db.text(f"SELECT * FROM {TABLE_NAME};")).fetchall()
        columns = ['city', 'date', 'budget', 'weather', 'itinerary']
        return pd.DataFrame(result, columns=columns)


def clear_search_history(engine=DEFAULT_ENGINE):
    """Deletes all entries in the search history table."""
    with engine.begin() as conn:
        conn.execute(db.text(f"DELETE FROM {TABLE_NAME};"))


def view_search_history():
    """Displays the search history in a user-friendly format."""
    df = get_search_history()
    if df.empty:
        print("\nNo search history found.\n")
        return

    # Display summary list
    print("\nSearch History:")
    for idx, row in df.iterrows():
        print(f"{idx + 1}. {row['city']} on {row['date']} (Budget: ${row['budget']})")

    try:
        selection = int(input("\nEnter number to view full itinerary (or 0 to cancel): "))
        if selection == 0:
            return
        selected = df.iloc[selection - 1]
        print("\nFull Details:")
        print(f"City: {selected['city']}")
        print(f"Date: {selected['date']}")
        print(f"Budget: ${selected['budget']}")
        print(f"Weather: {selected['weather']}")
        print("\nItinerary:\n")
        print(selected['itinerary'])

    except (ValueError, IndexError):
        print("Invalid selection. Please try again.")
