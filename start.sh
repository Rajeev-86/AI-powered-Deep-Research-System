#!/bin/bash

# Quick Start Script for Research System with Frontend

echo "=========================================="
echo " Research System - Full Stack Startup"
echo "=========================================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo " Virtual environment not found!"
    echo "Please create one first: python -m venv venv"
    exit 1
fi

# Check Node.js version
NODE_VERSION=$(node --version 2>/dev/null | cut -d'v' -f2 | cut -d'.' -f1)
if [ -z "$NODE_VERSION" ] || [ "$NODE_VERSION" -lt 20 ]; then
    echo "  Node.js 20+ required (current: $(node --version 2>/dev/null || echo 'not found'))"
    echo ""
    echo "To install Node.js 20+, run: ./setup_node.sh"
    echo "Then restart this script."
    exit 1
fi

# Load NVM if available
if [ -s "$HOME/.nvm/nvm.sh" ]; then
    export NVM_DIR="$HOME/.nvm"
    source "$NVM_DIR/nvm.sh"
fi

# Kill any existing servers
echo " Cleaning up existing servers..."
pkill -f "python api_server.py" 2>/dev/null || true
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
lsof -ti:3000 | xargs kill -9 2>/dev/null || true
sleep 1

# Activate virtual environment
echo " Activating virtual environment..."
source venv/bin/activate

# Install API dependencies if needed
echo " Installing backend dependencies..."
pip install -q -r requirements-api.txt

# Start backend server in background
echo ""
echo " Starting FastAPI backend server..."
echo " Backend logs will be shown below (and saved to backend.log)"
echo ""
python api_server.py 2>&1 | tee backend.log &
BACKEND_PID=$!

# Wait for backend to start
echo " Waiting for backend to initialize..."
sleep 5

# Check if backend is running
if curl -s http://localhost:8000/ > /dev/null; then
    echo " Backend server running at http://localhost:8000"
    echo " API Documentation: http://localhost:8000/docs"
else
    echo " Backend server failed to start"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

# Start frontend
echo ""
echo " Starting Next.js frontend..."
cd frontend

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo " Installing frontend dependencies..."
    npm install
fi

echo ""
echo "=========================================="
echo " System Ready!"
echo "=========================================="
echo ""
echo " Frontend: http://localhost:3000"
echo " Backend:  http://localhost:8000"
echo " API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"
echo "=========================================="
echo ""

# Start frontend (this will run in foreground)
npm run dev

# Cleanup on exit
trap "echo ''; echo 'Stopping services...'; kill $BACKEND_PID 2>/dev/null; exit" INT TERM
