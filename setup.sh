#!/bin/bash
echo "Setting up the project..."

# Navigate to the script's directory to ensure correct paths
cd "$(dirname "$0")"

# Create a virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies from code/requirements.txt
if [ -f "myapp/requirements.txt" ]; then
    pip install -r myapp/requirements.txt
else
    echo "ERROR: myapp/requirements.txt not found! Make sure it exists."
    exit 1
fi

# Run Flask server
python3 myapp/app.py
