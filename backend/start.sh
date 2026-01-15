#!/bin/bash
set -e

# Activate virtual environment
# source venv/bin/activate

# Create default admin user (script reads from .env via pydantic-settings)
echo "Creating default admin user..."
python create_user.py || echo "User creation failed or user already exists"

# Start the application
exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
