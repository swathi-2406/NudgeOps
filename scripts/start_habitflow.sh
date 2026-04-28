#!/bin/bash
# HabitFlow + NudgeOps Full Stack Startup

set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "================================================"
echo " HabitFlow x NudgeOps"
echo "================================================"

# Backend
echo "[1/2] Starting NudgeOps backend on :8000..."
cd "$ROOT/backend"
[ ! -d "venv" ] && python3 -m venv venv
source venv/bin/activate 2>/dev/null || source venv/Scripts/activate
pip install -q -r requirements.txt
python ../scripts/demo_seed.py 2>/dev/null || true
uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
BACK_PID=$!

sleep 2

# HabitFlow
echo "[2/2] Starting HabitFlow app on :3001..."
cd "$ROOT/habitflow"
[ ! -d "node_modules" ] && npm install
npm run dev &
FRONT_PID=$!

echo ""
echo "================================================"
echo " Running!"
echo "   NudgeOps API:  http://localhost:8000"
echo "   API Docs:      http://localhost:8000/docs"
echo "   HabitFlow App: http://localhost:3001"
echo "================================================"
echo ""
echo "Press Ctrl+C to stop all..."
trap "kill $BACK_PID $FRONT_PID 2>/dev/null; exit" INT
wait
