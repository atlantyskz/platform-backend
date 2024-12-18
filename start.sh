#!/bin/bash

# Run Alembic migrations
echo "Running Alembic migrations..."
alembic upgrade head

# Start the application
echo "Starting the application..."
exec python -u main.py
