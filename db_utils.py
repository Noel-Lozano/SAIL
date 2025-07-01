import pandas as pd
import sqlalchemy as db

DB_NAME = 'search_history.db'
TABLE_NAME = 'user_searches'
DEFAULT_ENGINE = db.create_engine(f'sqlite:///{DB_NAME}')


def save_search(entry_dict, engine=DEFAULT_ENGINE):
    """ Takes a dictionary with search data and appends it to the database. """
    df = pd.DataFrame([entry_dict])
    df.to_sql(TABLE_NAME, con=engine, if_exists='append', index=False)


def get_search_history(engine=DEFAULT_ENGINE):
    """ Returns all saved searches as a DataFrame. """
    with engine.connect() as conn:
        result = conn.execute(db.text(f"SELECT * FROM {TABLE_NAME};")).fetchall()
        columns = ['city', 'date', 'budget', 'weather', 'itinerary']
        return pd.DataFrame(result, columns=columns)


def clear_search_history(engine=DEFAULT_ENGINE):
    """ Deletes all entries in the search history table. """
    with engine.connect() as conn:
        conn.execute(db.text(f"DELETE FROM {TABLE_NAME};"))
