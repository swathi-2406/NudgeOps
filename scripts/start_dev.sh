#!/bin/bash
# NudgeOps Dev Startup Script
# Starts backend (FastAPI) + frontend (Vite) — Redis must be running

set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "⬡ NudgeOps Dev Startup"
echo "======================"

# Backend
echo ""
echo "→ Starting backend..."
cd "$ROOT/backend"
[ ! -d "venv" ] && python -m venv venv && echo "  Created virtualenv"
source venv/bin/activate || source venv/Scripts/activate 2>/dev/null
pip install -q -r requirements.txt
echo "  Seeding demo data..."
python ../scripts/demo_seed.py 2>/dev/null || true
uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
echo "  Backend PID: $BACKEND_PID"

# Frontend
echo ""
echo "→ Starting frontend..."
cd "$ROOT/frontend"
[ ! -d "node_modules" ] && npm install
npm run dev &
FRONTEND_PID=$!
echo "  Frontend PID: $FRONTEND_PID"

echo ""
echo "✅ NudgeOps is running!"
echo "   API:      http://localhost:8000"
echo "   Docs:     http://localhost:8000/docs"
echo "   Frontend: http://localhost:3000"
echo "   Metrics:  http://localhost:8000/metrics"
echo ""
echo "Press Ctrl+C to stop..."
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT
wait
