#!/bin/bash
set -e

# Create default admin user if env vars are set
if [ -n "$DEFAULT_ADMIN_EMAIL" ] && [ -n "$DEFAULT_ADMIN_PASSWORD" ]; then
    echo "Creating default admin user..."
    python create_user.py || echo "User creation failed or user already exists"
fi

# Start the application
exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
