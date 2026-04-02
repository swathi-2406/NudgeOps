@echo off
REM NudgeOps Dev Startup — Windows

echo NudgeOps Dev Startup
echo ====================

cd %~dp0..\backend
if not exist venv (
    python -m venv venv
)
call venv\Scripts\activate
pip install -q -r requirements.txt
python ..\scripts\demo_seed.py
start "NudgeOps Backend" cmd /k "call venv\Scripts\activate && uvicorn main:app --host 0.0.0.0 --port 8000 --reload"

cd %~dp0..\frontend
if not exist node_modules npm install
start "NudgeOps Frontend" cmd /k "npm run dev"

echo.
echo NudgeOps started!
echo   API:      http://localhost:8000
echo   Docs:     http://localhost:8000/docs
echo   Frontend: http://localhost:3000
