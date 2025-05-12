import json
from backend.db.connection import *
from backend.db.utils import *

def patient_exists(patient_id):
    query = 'SELECT * FROM patients WHERE patient_id = %s'
    result = execute_query(query, (patient_id,), fetch_one=True)
    return result is not None

def insert_patient_into_db(patient_info):
    query = """
        INSERT INTO patients (
            patient_id, gender, age, heart_rhythm, conduction_system_disease,
            cardiac_pacing, hypertrophies, ischemia, repolarization_abnormalities
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    params = (
        patient_info['anonymous_id'],
        patient_info['sex'],
        patient_info['age'],
        patient_info['rhythm'],
        json.dumps(patient_info.get('conduction_system_disease', [])),
        json.dumps(patient_info.get('cardiac_pacing', [])),
        json.dumps(patient_info.get('hypertrophies', [])),
        json.dumps(patient_info.get('ischemia', [])),
        patient_info['repolarization_abnormalities']
    )
    execute_query(query, params)
    
# -------------------- Fetch functions --------------------  

def fetch_all_patients():
    return fetch_from_db('SELECT * FROM patients')

def fetch_patient_by_id(patient_id):
    patient = fetch_from_db('SELECT * FROM patients WHERE patient_id = %s', (patient_id,))
    if not patient.get('data'):  # No patient found, return an error
        return {"error": "Patient not found"}
    return patient

# --------------------- Delete Functions ---------------------
def delete_patient_by_id(patient_id):
    # Trigger already existed in database, calling this function will also delete the corresponding ecg data of that patient
    
    try:
        # Check if the patient exists before attempting to delete
        if not patient_exists(patient_id):
            return {"success": False, "error": "Patient not found"}

        query = 'DELETE FROM patients WHERE patient_id = %s'
        execute_query(query, (patient_id,))
        
        return {"success": True, "message": "Patient deleted successfully"}
    except Exception as e:
        return {"success": False, "error": f"An error occurred: {str(e)}"}