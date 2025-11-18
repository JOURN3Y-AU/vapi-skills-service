#!/bin/bash
# Start the FastAPI server with the correct venv

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Activate the virtual environment
source "$SCRIPT_DIR/venv/bin/activate"

# Run uvicorn with explicit python path
exec "$SCRIPT_DIR/venv/bin/python3" -m uvicorn app.main:app --reload --port 8000
