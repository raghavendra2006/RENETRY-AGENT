#!/usr/bin/env bash
# Render Build Script
set -o errexit

pip install --upgrade pip
pip install -r requirements.txt

# Create uploads directory
mkdir -p static/uploads

# Initialize/seed the database
python -c "from database import init_db; init_db()"
python seed_data.py
