from backend.db.ecg import *

def validate_ecg_data(ecg_data):
    required_keys = ['time', 'signals', 'maxima_graph_data', 'minima_graph_data', 'baselines_graph_data']
    for key in required_keys:
        if key not in ecg_data:
            return {"success": False, "error": f"Missing required key: {key}"}
    return {"success": True}

def add_ecg_data(patient_id, ecg_data):
    validation_result = validate_ecg_data(ecg_data)
    if not validation_result["success"]:
        return validation_result

    if ecg_data_exists(patient_id):
        return {"success": False, "ecg_exists": True}

    try:
        insert_ecg_data_into_db(patient_id, ecg_data)
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}