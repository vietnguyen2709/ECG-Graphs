from flask import jsonify
from backend.db.result_vector import *

def validate_result_vector_data(data):
    if "anonymous_id" not in data or not str(data['anonymous_id']).isdigit():
        return {"success": False, "error": "Missing or invalid anonymous_id"}, 400

    lead_data_list = data.get('leadDataArray', [])
    if not isinstance(lead_data_list, list):
        return {"success": False, "error": "Invalid leadDataArray format"}, 400

    return {"success": True}

def add_result_vector(data):
    validation_result = validate_result_vector_data(data)
    if isinstance(validation_result, tuple):
        # error case
        error_response, status_code = validation_result
        return jsonify(error_response), status_code

    # Process the result vector data
    try:
        processed_data = process_result_vector(data)
        insert_result_vector_into_db(processed_data)
        return {"success": True, "message": "Result vector stored successfully"}
    except Exception as e:
        return {"success": False, "error": str(e)}, 500

def process_result_vector(data):
    processed_data = {
        "anonymous_id": int(data['anonymous_id']),
        "beat_data": process_lead_data(data.get('leadDataArray', []))
    }
    return processed_data

def process_lead_data(lead_data_list):
    beat_data = {"Lead 1": {}, "Lead 2": {}, "Lead 3": {}} #ensure all expected keys exist. empty dictionaries for missing leads avoiding key errors.
    for lead_data in lead_data_list:
        lead = lead_data.get('lead')
        beat_data[f"Lead {lead}"] = {
            "start_time": lead_data.get('startTime'),
            "end_time": lead_data.get('endTime'),
            "avg_baseline": lead_data.get('avgBaseline'),
            "max_beat": lead_data.get('maxBeat'),
            "min_beat": lead_data.get('minBeat'),
            "corrected_max_peak": lead_data.get('correctedMaxPeak'),
            "corrected_min_peak": lead_data.get('correctedMinPeak'),
            "lead_vector": lead_data.get('leadVector')
        }
    return beat_data
