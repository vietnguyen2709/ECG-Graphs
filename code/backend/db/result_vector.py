import json
from datetime import datetime
from backend.db.utils import *

def insert_result_vector_into_db(processed_data):
    query = """
        INSERT INTO ecg_beat_selection (
            patient_id, lead_1_data, lead_2_data, lead_3_data, created_at
        ) VALUES (%s, %s, %s, %s, %s)
    """
    params = (
        processed_data['anonymous_id'],
        json.dumps(processed_data['beat_data']['Lead 1']),
        json.dumps(processed_data['beat_data']['Lead 2']),
        json.dumps(processed_data['beat_data']['Lead 3']),
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    execute_query(query, params)
    
# -------------------- Fetch functions --------------------  
def fetch_all_result_vectors():
    return fetch_from_db('SELECT * FROM ecg_beat_selection')

def fetch_result_vectors_by_patient_id(patient_id):
    return fetch_from_db('SELECT * FROM ecg_beat_selection WHERE patient_id = %s', (patient_id,))
