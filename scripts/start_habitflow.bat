@echo off
REM HabitFlow + NudgeOps Full Stack Startup

echo ================================================
echo  HabitFlow x NudgeOps
echo ================================================
echo.

REM 1. Backend (NudgeOps API)
echo [1/2] Starting NudgeOps backend on :8000...
cd %~dp0..\backend
if not exist venv (
    echo Creating virtualenv...
    python -m venv venv
)
call venv\Scripts\activate
pip install -q -r requirements.txt
python ..\scripts\demo_seed.py >nul 2>&1
start "NudgeOps Backend" cmd /k "call venv\Scripts\activate && uvicorn main:app --reload --port 8000"
timeout /t 3 /nobreak >nul

REM 2. HabitFlow React app
echo [2/2] Starting HabitFlow app on :3001...
cd %~dp0..\habitflow
if not exist node_modules (
    echo Installing dependencies...
    npm install
)
start "HabitFlow App" cmd /k "npm run dev"

echo.
echo ================================================
echo  Running!
echo    NudgeOps API:  http://localhost:8000
echo    API Docs:      http://localhost:8000/docs
echo    HabitFlow App: http://localhost:3001
echo    NudgeOps UI:   http://localhost:3000
echo ================================================
