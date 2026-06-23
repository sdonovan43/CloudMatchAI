#!/bin/bash

# ----------------------------------------
# Virtual Environment Setup Script
# ----------------------------------------

# Exit on error
set -e

echo "Creating Python virtual environment..."
python3 -m venv env

echo "Activating virtual environment..."
source env/bin/activate

echo "Upgrading pip..."
pip install --upgrade pip

echo "Installing dependencies from requirements.txt..."
pip install -r requirements.txt

echo "Installing Playwright browsers..."
playwright install

echo "Setup complete. Virtual environment is ready."
echo "To activate later, run: source env/bin/activate"
