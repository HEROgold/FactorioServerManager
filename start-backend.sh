#!/bin/bash
# Start the FastAPI backend server

echo "Starting Factorio Server Manager API..."
echo "API will be available at http://localhost:8000"
echo "API documentation at http://localhost:8000/docs"
echo ""

cd src
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
