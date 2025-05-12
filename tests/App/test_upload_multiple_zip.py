import os
import pytest
from flask import Flask, jsonify
import io
from io import BytesIO
from unittest.mock import patch
import zipfile

import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../code")))
from backend.app import app

@pytest.fixture
def client():
    with app.test_client() as client:
        yield client

# test Missing file part in the request
def test_upload_files_missing_file_part(client):
    response = client.post('/uploads', data={})
    assert response.status_code == 400
    assert response.json == {"error": "No files part in the request"}

#test No files selected in the request
def test_upload_files_no_selected_files(client):
    data = {
        'files[]': (io.BytesIO(b"dummy content"), '')  # empty filename
    }
    response = client.post('/uploads', data=data)
    assert response.status_code == 400
    assert response.json == {"error": "No selected files"}

#test Invalid file type
def test_upload_files_invalid_file_type(client):
    data = {
        'files[]': (BytesIO(b"Not a zip file"), 'test.txt')
    }
    response = client.post('/uploads', data=data, content_type='multipart/form-data')
    assert response.status_code == 200
    assert response.json == [{"file": 'test.txt', "error": "Please upload a ZIP file containing ECG data."}]


@patch('os.remove')
@patch('zipfile.ZipFile', side_effect=zipfile.BadZipFile("Bad zip"))
@patch('werkzeug.datastructures.FileStorage.save')
def test_upload_files_bad_zipfile(mock_save, mock_zipfile, mock_remove, client):
    bad_zip = BytesIO(b"This is not a real zip file")
    bad_zip.filename = "corrupted.zip"

    data = {
        'files[]': (bad_zip, bad_zip.filename)
    }

    response = client.post('/uploads', data=data, content_type='multipart/form-data')

    assert response.status_code == 200
    assert len(response.json) == 1
    assert response.json[0]["file"] == "corrupted.zip"
    assert response.json[0]["error"] == "Uploaded file is not a valid ZIP archive."


# test Valid ZIP file
@patch('backend.app.process_and_store_ecg_data')
@patch('werkzeug.datastructures.FileStorage.save')
@patch('zipfile.ZipFile')
@patch('os.remove')  # mock os.remove to bypasses the actual filesystem interaction and focus on file upload and ZIP extraction
def test_upload_files_valid_zip(mock_remove, mock_zipfile, mock_save, mock_process_and_store, client):
    with app.app_context():
        mock_process_and_store.return_value = jsonify({"message": "Success"})
    
        mock_save.return_value = None
        
        mock_zip = mock_zipfile.return_value.__enter__.return_value
        mock_zip.extractall.return_value = None
    
        # create mock zip file content
        data = {
            'files[]': (io.BytesIO(b"PK\x03\x04" + b'Fake content'), 'valid.zip')
        }
    
        #test a valid ZIP file upload
        response = client.post('/uploads', data=data, content_type='multipart/form-data')
 
        assert response.status_code == 200
        assert len(response.json) == 1
        assert response.json[0]["file"] == "valid.zip"
        assert "result" in response.json[0]
        assert response.json[0]["result"] == {"message": "Success"}
