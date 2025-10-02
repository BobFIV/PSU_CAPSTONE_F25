#!/bin/bash

# Navigate to demoApp folder (relative to repo root)
cd "$(dirname "$0")/demoApp" || exit

echo "Creating virtual environment..."
python3 -m venv venv

echo "Installing dependencies into virtual environment..."
venv/bin/pip install --upgrade pip
venv/bin/pip install -r requirements.txt

echo "Setup complete."
echo "You can now use the Makefile to run the app:"
echo "  make run       # Start the web server"
echo "  make fakedevice # Run the fake device simulator"
