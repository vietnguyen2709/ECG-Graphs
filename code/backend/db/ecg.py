import json
from backend.db.connection import *
from backend.db.utils import *
from backend.db.utils import execute_query

def ecg_data_exists(patient_id):
    query = 'SELECT * FROM ecg_data WHERE patient_id = %s'
    result = execute_query(query, (patient_id,), fetch_one=True)
    return result is not None

def insert_ecg_data_into_db(patient_id, ecg_data):
    query = """
        INSERT INTO ecg_data (
            patient_id, time_data, signal_raw_data, maxima_data,
            minima_data, baseline_data
        ) VALUES (%s, %s, %s, %s, %s, %s)
    """
    params = (
        patient_id,
        json.dumps(ecg_data['time']),
        json.dumps(ecg_data['signals']),
        json.dumps(ecg_data['maxima_graph_data']),
        json.dumps(ecg_data['minima_graph_data']),
        json.dumps(ecg_data['baselines_graph_data'])
    )
    execute_query(query, params)
    
# -------------------- Fetch functions --------------------
def fetch_all_ecg_data():
    return fetch_from_db('SELECT * FROM ecg_data')

def fetch_ecg_data_by_patient_id(patient_id):
    query = "SELECT * FROM ecg_data WHERE patient_id = %s"
    result = execute_query(query, (patient_id,), fetch_one=True)
    if not result:
        return None

    return {
        "time": json.loads(result["time_data"]),
        "signals": json.loads(result["signal_raw_data"]),
        "maxima_graph_data": json.loads(result["maxima_data"]),
        "minima_graph_data": json.loads(result["minima_data"]),
        "baselines_graph_data": json.loads(result["baseline_data"])
    }
