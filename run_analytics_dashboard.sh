#!/bin/bash

# EduSense AI - Engagement Analytics Dashboard Launcher
# This script starts the Flask API server and opens the dashboard

echo "=========================================="
echo "🎓 EduSense AI - Engagement Analytics"
echo "=========================================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed"
    exit 1
fi

# Check if required files exist
if [ ! -f "best_model_state.bin" ]; then
    echo "❌ Model file 'best_model_state.bin' not found"
    exit 1
fi

if [ ! -f "api_server.py" ]; then
    echo "❌ API server file 'api_server.py' not found"
    exit 1
fi

# Check if students directory exists
if [ ! -d "students" ]; then
    echo "⚠️  Warning: 'students' directory not found"
    echo "   Run the tracking system first to collect student images"
    echo ""
fi

# Install dependencies if needed
echo "📦 Checking dependencies..."
pip3 install -q flask flask-cors torch torchvision pillow tqdm 2>/dev/null

echo "✅ Dependencies checked"
echo ""

# Start the API server
echo "🚀 Starting API server..."
echo "   Server will run on http://localhost:5001"
echo ""
echo "📊 Dashboard will be available at:"
echo "   http://localhost:5001"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""
echo "=========================================="
echo ""

# Kill any existing process on port 5001
lsof -ti:5001 | xargs kill -9 2>/dev/null

# Run the server
python3 api_server.py --host 0.0.0.0 --port 5001
