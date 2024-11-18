#!/bin/bash

set -e  # Exit immediately if a command exits with a non-zero status

echo "Running database migrations..."
poetry run python migrations.py

echo "Starting application processes..."
# Run the main command (CMD from the Dockerfile)
exec "$@"

