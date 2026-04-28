# ⬡ NudgeOps — MLOps Platform for Personalized Behavioral Intervention Policies

An AI-driven behavioral intervention platform that learns which motivational strategy works best for each individual user, updating policies over time using multi-armed bandit algorithms and feedback signals.

> For one user, streaks work. For another, loss framing. For another, dark humor.  
> NudgeOps learns this — and adapts.

---

## Architecture

```
nudgeops/
├── backend/                  # FastAPI + SQLite + Celery
│   ├── api/routes/           # REST endpoints (users, bandit, policies, experiments, monitoring, audit)
│   ├── ml/
│   │   ├── bandit/           # Thompson Sampling, UCB, ε-Greedy, Contextual LinUCB
│   │   ├── embeddings/       # User behavioral embeddings + feature store
│   │   └── evaluation/       # Offline policy eval + A/B test statistical analysis
│   ├── services/             # Bandit orchestration, monitoring, audit
│   └── tasks/                # Celery background jobs (retraining, snapshots, embeddings)
├── frontend/                 # React + Vite dashboard
│   └── src/pages/            # Dashboard, Users, Interventions, A/B Tests, Policies, Monitoring, Audit
├── scripts/                  # Dev startup + demo data seeder
└── docker-compose.yml        # Redis + Backend + Frontend + Worker
```

---

## Quick Start (Local — no Docker needed)

### Prerequisites
- Python 3.10+
- Node.js 18+
- Redis running locally: `redis-server` (or `brew install redis && redis-server`)

### 1. Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python ../scripts/demo_seed.py  # seed demo users + data
uvicorn main:app --reload --port 8000
```

### 2. Frontend
```bash
cd frontend
npm install
npm run dev                     # starts at http://localhost:3000
```

### 3. One-command startup (Linux/Mac)
```bash
chmod +x scripts/start_dev.sh
./scripts/start_dev.sh
```

### 4. Windows
```bat
scripts\start_dev.bat
```

### 5. With Docker (Redis only)
```bash
docker run -d -p 6379:6379 redis:7-alpine
# then follow steps 1 + 2 above
```

---

## MLOps Features

| Feature | Implementation |
|---------|---------------|
| **Event logging pipeline** | `POST /api/v1/events/` · batch ingest · background cache invalidation |
| **Feature store** | Per-user behavioral features · Redis cache · SQLite persistence |
| **Contextual bandit** | Thompson Sampling, UCB, ε-Greedy, Contextual LinUCB |
| **User embeddings** | 32-dim behavioral vectors · cosine similarity nearest-neighbor |
| **Offline policy eval** | Completion/engagement/reward metrics · confidence intervals |
| **A/B testing** | Two-sample t-test · Cohen's d · p-value · winner detection |
| **Policy registry** | Versioned policies · promote · rollback · shadow mode |
| **Retraining pipeline** | Celery beat scheduler · triggered on feedback accumulation |
| **Failure detection** | Rolling reward window · per-arm failure flagging · recovery |
| **Fairness checks** | Per-user intervention distribution caps (max 60% single type) |
| **Audit logs** | Every system action logged with actor, resource, outcome |
| **Prometheus metrics** | `/metrics` endpoint · request count/latency counters |

---

## API Reference

Full interactive docs at `http://localhost:8000/docs`

### Key Endpoints

```
POST /api/v1/bandit/nudge          # Select best intervention for a user
POST /api/v1/bandit/feedback       # Record user response (reward signal)
GET  /api/v1/bandit/state/{uid}    # View per-user arm states

POST /api/v1/events/               # Ingest single event
POST /api/v1/events/batch          # Ingest event batch

GET  /api/v1/monitoring/metrics    # System-wide platform metrics
GET  /api/v1/monitoring/fairness   # Fairness distribution check
GET  /api/v1/policies/{id}/evaluate  # Offline policy evaluation

POST /api/v1/experiments/          # Create A/B experiment
POST /api/v1/experiments/{id}/start
POST /api/v1/experiments/{id}/conclude
GET  /api/v1/experiments/{id}/results

GET  /api/v1/features/user/{uid}    # User feature vector
POST /api/v1/features/user/{uid}/embedding  # Compute behavioral embedding
GET  /api/v1/audit/                 # Human-readable audit trail
```

---

## Intervention Types

| Strategy | Manipulativeness | Example |
|----------|-----------------|---------|
| Positive Reinforcement | 1/10 | "Amazing work! You completed 80% of your goal." |
| Streak Tracker | 2/10 | "🔥 Day 7 streak! Don't break the chain." |
| Dark Humor Reminder | 2/10 | "⚰️ You're not getting younger. Do the thing." |
| Implementation Intention | 2/10 | "When you finish lunch, you'll spend 10 mins on this." |
| Micro Challenge | 2/10 | "⚡ Today's challenge: just 5 minutes." |
| Public Accountability | 4/10 | "Your network saw you commit to this." |
| Commitment Device | 5/10 | "You committed to this yesterday." |
| Social Proof | 5/10 | "1,247 people like you finished this today." |
| Loss Framing | 7/10 | "⚠️ You're losing 3 days of progress by skipping." |

Fairness guard: no single strategy can exceed **60%** of nudges per user.

---

## Background Jobs (Celery)

| Task | Schedule | Purpose |
|------|----------|---------|
| `take_monitoring_snapshot` | Every 15 min | Capture system metrics |
| `refresh_all_embeddings` | Every 6h | Recompute user behavioral vectors |
| `check_and_retrain` | Every 12h | Evaluate + retrain active policy if needed |
| `analyze_running_experiments` | Every 3h | Auto-analyze A/B tests |
| `detect_and_flag_failures` | On demand | Scan bandit arms for failure modes |

Start the worker:
```bash
cd backend
celery -A tasks.celery_app worker --loglevel=info
celery -A tasks.celery_app beat --loglevel=info
```

---

## Environment Variables

```env
DATABASE_URL=sqlite+aiosqlite:///./nudgeops.db
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-secret-here
ENVIRONMENT=development

BANDIT_EPSILON=0.15
BANDIT_UCB_ALPHA=1.0
AB_TEST_MIN_SAMPLE_SIZE=30
MAX_SINGLE_INTERVENTION_SHARE=0.60
```

---

## Tech Stack

**Backend:** FastAPI · SQLAlchemy (async) · SQLite/aiosqlite · Redis · Celery · NumPy · SciPy · scikit-learn · Prometheus · structlog  
**Frontend:** React 18 · Vite · React Router · Recharts · Lucide React  
**ML:** Thompson Sampling · UCB1 · ε-Greedy · Contextual LinUCB · Beta-Bernoulli conjugate updates · two-sample t-test  

---

Built by [Your Name] · NudgeOps v1.0.0

---

## HabitFlow — Full Habit Tracker App

A fully functional mobile-style habit tracking app built on top of NudgeOps.

**Start it:**
```bash
# Windows
scripts\start_habitflow.bat

# Mac/Linux
./scripts/start_habitflow.sh
```

Then open **http://localhost:3001**

See `habitflow/README.md` for full documentation.

### Screens
- **Login / Signup** — JWT auth, persistent sessions
- **Home** — Daily habits, completion toggle, streak, AI nudge inline
- **Nudge Center** — Request nudge, submit feedback, view history
- **Stats** — 30-day heatmap, weekly chart, streak records, nudge effectiveness
- **Social** — Follow users, activity feed with likes, discover people
- **Profile** — Edit name/bio/avatar color, sign out
- **Habit Detail** — Per-habit completion chart and history
