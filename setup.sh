#!/bin/bash

# Navigate to demoApp folder (relative to repo root)
cd "$(dirname "$0")/demoApp" || exit

echo "Creating virtual environment..."
python3 -m venv venv

echo "Activating virtual environment and installing dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "Setup complete."
echo "To start the server, run:"
echo "source venv/bin/activate && python manage.py runserver"
