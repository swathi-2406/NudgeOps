# HabitFlow — Fully Functional Habit Tracker

A complete mobile-style habit tracking app powered by the NudgeOps AI backend.
Every nudge is personalized using a contextual Thompson Sampling bandit that
learns which motivational strategy works best for each individual user.

## Features

**Auth**
- Signup / login with JWT tokens
- Persistent sessions (token in localStorage)

**Habits**
- Create habits with custom icon, color, frequency, days, reminder time
- Mark complete / uncomplete per day
- Habit categories (Health, Mind, Learning, Social)
- Public / private habit visibility

**Streaks & Stats**
- Real-time streak calculation from completion history
- 30-day activity heatmap
- Per-habit completion history with chart
- Nudge effectiveness metrics

**AI Nudges (NudgeOps)**
- Personalized nudge via Thompson Sampling bandit
- 10 intervention strategy types
- 5 feedback signals (completed / engaged / ignored / dismissed / negative)
- Full nudge history with reward tracking

**Social**
- Follow / unfollow other users
- Activity feed (completions, streak milestones, joins)
- Like activity feed posts
- Discover users with search
- Public profile pages

## Quick Start

**Step 1** — Start the NudgeOps backend (required):
```powershell
cd backend
pip install -r requirements.txt
python ../scripts/demo_seed.py
uvicorn main:app --reload --port 8000
```

**Step 2** — Start HabitFlow:
```powershell
cd habitflow
npm install
npm run dev
```

**Step 3** — Open http://localhost:3001

Or use the one-command script:
```bash
./scripts/start_habitflow.sh      # Mac/Linux
scripts\start_habitflow.bat        # Windows
```

## How the AI works

When you tap "Get AI nudge":
1. HabitFlow calls `POST /api/v1/habitflow/nudge/request`
2. NudgeOps looks up your bandit arm states (one Beta distribution per strategy)
3. Thompson Sampling: samples from each Beta(α, β) distribution, picks the max
4. Returns the selected intervention message
5. You respond with one of 5 signals → NudgeOps updates α and β
6. Over time, your best strategy rises to the top

**No training needed.** The bandit learns live from your feedback.

## API endpoints added

All under `POST/GET /api/v1/habitflow/`:

| Method | Path | Description |
|--------|------|-------------|
| POST | /auth/signup | Create account |
| POST | /auth/login | Login, get JWT |
| GET  | /auth/me | Current user + stats |
| GET  | /habits | List habits with today's completions |
| POST | /habits | Create habit |
| PATCH | /habits/:id | Update habit |
| DELETE | /habits/:id | Soft-delete habit |
| POST | /habits/:id/complete | Mark complete |
| DELETE | /habits/:id/complete/:date | Uncomplete |
| GET  | /habits/:id/history | Completion history + chart data |
| GET  | /habits/completions/range | Date range completions |
| POST | /nudge/request | Get personalized nudge |
| POST | /nudge/feedback | Submit feedback signal |
| GET  | /nudge/history | Nudge history |
| GET  | /stats | Full user stats + heatmap |
| GET  | /social/feed | Following feed |
| GET  | /social/discover | Find users |
| POST | /social/follow/:id | Follow user |
| DELETE | /social/follow/:id | Unfollow |
| POST | /social/like/:id | Like/unlike activity |
| GET  | /social/profile/:username | Public profile |
| PATCH | /profile | Update profile |
| GET  | /categories | Habit categories |

## Tech stack

React 18 · Vite · React Router · Zustand · Recharts · Lucide · date-fns
FastAPI · SQLAlchemy · SQLite · JWT auth · passlib/bcrypt
