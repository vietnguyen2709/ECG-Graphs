from backend.db.db_setup import *

def get_db_connection_safe():
    try:
        return get_db_connection()
    except Exception as e:
        raise Exception(f"Database connection error: {str(e)}")