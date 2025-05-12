from backend.db.connection import *

def fetch_from_db(query, params=None):
    try:
        connection = get_db_connection_safe()
        with connection.cursor() as cursor:
            cursor.execute(query, params or ())
            result = cursor.fetchall()
        connection.close()
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}
    
def execute_query(query, params=None, fetch_one=False):
    connection = get_db_connection_safe()
    try:
        with connection.cursor() as cursor:
            cursor.execute(query, params or ())
            if fetch_one:
                result = cursor.fetchone()
            else:
                result = cursor.fetchall()
        connection.commit()
        return result
    finally:
        connection.close()
