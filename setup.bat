@echo off
echo Setting up the project...

:: Navigate to the script's directory to ensure correct paths
cd %~dp0

:: Create virtual environment
python -m venv venv
call venv\Scripts\activate

:: Install dependencies from requirements.txt (at root level)
if exist "requirements.txt" (
    pip install -r requirements.txt
) else (
    echo ERROR: requirements.txt not found! Make sure it exists in the root directory.
    exit /b 1
)

:: Run Flask server
python code/backend/app.py
