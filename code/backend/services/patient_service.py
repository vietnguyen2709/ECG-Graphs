from backend.db.patient import *
from backend.db.ecg import *
from backend.services.ecg_service import *

def validate_patient_info(patient_info):
    if "anonymous_id" not in patient_info:
        return {"success": False, "error": "Missing anonymous_id"}
    return {"success": True}

def add_patient(patient_info):
    validation_result = validate_patient_info(patient_info)
    if not validation_result["success"]:
        return validation_result

    # Check if the patient already exists
    if patient_exists(patient_info['anonymous_id']):
        return {"success": False, "patient_exists": True}

    # Insert the patient into the database
    try:
        insert_patient_into_db(patient_info)
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}

def store_patient_and_ecg_data(data):
    try:
        # Add the patient
        patient_result = add_patient(data['patient_info'])
        if not patient_result["success"]:
            if patient_result.get("patient_exists"):
                print("\033[93mPatient already exists in the database, only inserting ECG data\033[0m")  # Yellow text
            else:
                print("\033[91mError adding patient: {}\033[0m".format(patient_result["error"]))  # Red text
                return {"success": False, "error": patient_result["error"]}
        else:
            print("\033[92mNew Patient added successfully\033[0m") # Green text

        # Add the ECG data
        ecg_result = add_ecg_data(data['patient_info']['anonymous_id'], data)
        if not ecg_result["success"]:
            if ecg_result.get("ecg_exists"):
                print("\033[93mECG data already exists in the database, skipping insertion\033[0m")  # Yellow text
                return {"success": False, "ecg_exists": True}
            else:
                print("\033[91mError adding ECG data: {}\033[0m".format(ecg_result["error"]))  # Red text
                #return ecg_result
                return {"success": False, "error": ecg_result["error"]}
        else:
            print("\033[92mECG data added successfully\033[0m") # Green text
            
        return {"success": True, "message": "Patient and ECG data stored successfully"}

    except Exception as e:
        print("\033[91mError: {}\033[0m".format(str(e)))  # Red text
        return {"success": False, "error": str(e)}
