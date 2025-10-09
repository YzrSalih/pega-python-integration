#!/bin/bash

# Pega-Python Integration Startup Script

echo "🚀 Starting Pega-Python Integration Server..."

# Virtual environment check
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Load environment variables
if [ -f ".env" ]; then
    echo "🔧 Loading environment variables..."
    export $(grep -v '^#' .env | xargs)
fi

# Start server
echo "🌟 Starting FastAPI server..."
cd backend
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
