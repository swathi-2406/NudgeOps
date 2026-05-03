# ⬡ NudgeOps × HabitFlow

> An AI-powered habit tracker that learns which motivational strategy works best for *you* — backed by a full MLOps platform built for personalized behavioral intervention.

**Not all motivation is equal.** Streaks work for some people. Loss framing works for others. Dark humor works for others. Most apps treat everyone the same. NudgeOps doesn't.

---

## 🔗 Live Links

| | URL |
|---|---|
| 📱 **HabitFlow App** | [habitflow-beta.netlify.app](https://habitflow-beta.netlify.app) |
| 📊 **NudgeOps MLOps Dashboard** | [nudgeops-dashboard.netlify.app](https://nudgeops-dashboard.netlify.app) |
| ⚡ **Backend API** | [nudgeops-api.onrender.com](https://nudgeops-api.onrender.com) |
| 📖 **API Docs** | Available in development mode only |

**Install HabitFlow on your phone:**
- iPhone → Open in Safari → Share → "Add to Home Screen"
- Android → Open in Chrome → Menu → "Add to Home Screen"

---

## 🧠 How the AI works

Every user has **10 bandit arms** — one per motivational strategy. Each arm is a Beta(α, β) distribution representing the system's belief about how effective that strategy is for that specific person.

```
New user — all arms start equal:
streak_tracker:          Beta(1, 1)  → 50% estimated success
dark_humor_reminder:     Beta(1, 1)  → 50% estimated success
loss_framing:            Beta(1, 1)  → 50% estimated success
...
```

**At nudge selection time — Thompson Sampling:**
1. Sample one value from each arm's Beta distribution
2. Pick the arm with the highest sample
3. Deliver that intervention to the user

**When the user responds:**

| Feedback | Reward | Update |
|---|---|---|
| Done it! | +1.0 | α increases strongly |
| Maybe | +0.5 | α increases slightly |
| Ignore | 0.0 | No change |
| Skip | −0.2 | β increases |
| Not helpful | −0.5 | β increases strongly |

**After 15–20 interactions:**
```
streak_tracker:      Beta(14, 3)  → 82% — this user loves streaks ✓
loss_framing:        Beta(2,  9)  → 18% — this user hates guilt trips ✗
dark_humor_reminder: Beta(6,  5)  → 55% — this user is neutral
```

The bandit has learned this user's motivational style — without any offline training, no GPU, no dataset. Pure online Bayesian updating.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                   User Interfaces                    │
│  HabitFlow PWA          NudgeOps Dashboard           │
│  (React + Vite)         (React + Vite)               │
│  habitflow-beta         nudgeops-dashboard           │
│  .netlify.app           .netlify.app                 │
└────────────────┬───────────────────┬────────────────┘
                 │                   │
                 ▼                   ▼
┌─────────────────────────────────────────────────────┐
│              FastAPI Backend (Render)                │
│  nudgeops-api.onrender.com                          │
│                                                     │
│  /api/v1/habitflow/   — HabitFlow app routes        │
│  /api/v1/bandit/      — Bandit engine               │
│  /api/v1/policies/    — Policy registry             │
│  /api/v1/experiments/ — A/B testing                 │
│  /api/v1/monitoring/  — System metrics              │
│  /api/v1/audit/       — Audit logs                  │
└──────────┬──────────────────────────────────────────┘
           │
     ┌─────┴──────┐
     ▼            ▼
PostgreSQL      Redis
(Render free)   (feature cache)
```

---

## ⚙️ MLOps Features

| Feature | Implementation |
|---|---|
| **Contextual Bandit** | Thompson Sampling, UCB1, ε-Greedy, LinUCB |
| **Feature Store** | 14 behavioral features · 30-day rolling window · Redis TTL cache |
| **User Embeddings** | 32-dim vectors · cosine similarity nearest-neighbor |
| **Offline Policy Eval** | Reward CI · completion rate · health score |
| **A/B Testing** | Two-sample t-test · Cohen's d · p-value · winner detection |
| **Policy Registry** | Versioned · promote · rollback · shadow mode |
| **Retraining Pipeline** | Celery beat · triggers on feedback accumulation |
| **Failure Detection** | Rolling reward window · per-arm failure flagging |
| **Fairness Constraints** | No strategy > 60% of nudges per user |
| **Audit Logging** | Every system action logged with actor + outcome |
| **Rate Limiting** | Per-IP limits on signup, login, nudge requests |
| **Prometheus Metrics** | Request count · latency histograms |

---

## 📱 HabitFlow — App Features

- **Auth** — JWT signup/login, persistent sessions, bcrypt passwords
- **Habits** — Create with custom icon, color, frequency, reminders, categories
- **Daily tracking** — Tap to complete, streak calculation, progress bar
- **AI Nudges** — Auto-delivered on app open (once/day), 5-signal feedback
- **Stats** — 30-day heatmap, weekly bar chart, nudge effectiveness metrics
- **Social** — Follow users, activity feed, likes, public profiles, discovery
- **PWA** — Installable on iOS and Android, offline support via service worker

---

## 🗂️ Project Structure

```
nudgeops/
├── backend/                    # FastAPI + SQLAlchemy + Celery
│   ├── api/routes/             # 10 route modules (users, bandit, policies...)
│   ├── ml/
│   │   ├── bandit/engine.py    # Thompson Sampling, UCB, ε-Greedy, LinUCB
│   │   ├── embeddings/         # Feature store + 32-dim user embeddings
│   │   └── evaluation/         # Offline policy eval + A/B test analysis
│   ├── services/               # Bandit orchestration, monitoring, audit
│   ├── tasks/celery_app.py     # 5 scheduled background jobs
│   └── db/models.py            # 17 SQLAlchemy models
│
├── habitflow/                  # React + Vite — user-facing app
│   └── src/pages/              # Login, Home, Nudge, Stats, Social, Profile
│
├── frontend/                   # React + Vite — MLOps dashboard
│   └── src/pages/              # Dashboard, Users, Interventions, Monitoring
│
└── scripts/
    └── demo_seed.py            # Seeds 8 demo users with synthetic data
```

---

## 🚀 Run Locally

**Prerequisites:** Python 3.10+, Node.js 18+, Redis

```bash
# 1. Backend
cd backend
pip install -r requirements.txt
python ../scripts/demo_seed.py
uvicorn main:app --reload --port 8000

# 2. HabitFlow app
cd habitflow
npm install
npm run dev        # → http://localhost:3001

# 3. NudgeOps dashboard
cd frontend
npm install
npm run dev        # → http://localhost:3000
```

---

## 🔬 Intervention Strategies

| Strategy | Manipulativeness | Example |
|---|---|---|
| Positive Reinforcement | 1/10 | "Amazing work! You're 80% there this week." |
| Streak Tracker | 2/10 | "🔥 Day 7! Don't break the chain." |
| Dark Humor | 2/10 | "⚰️ You're not getting younger. Do the thing." |
| Micro Challenge | 2/10 | "⚡ Just 5 minutes. Set a timer. Go." |
| Implementation Intention | 2/10 | "When you finish lunch, you'll spend 10 mins on this." |
| Public Accountability | 4/10 | "Your network saw you commit to this." |
| Commitment Device | 5/10 | "You committed to this yesterday." |
| Social Proof | 5/10 | "1,247 people like you finished this today." |
| Loss Framing | 7/10 | "⚠️ You're losing 3 days of progress by skipping." |

Fairness guard: no single strategy exceeds **60%** of nudges per user.
Cold-start guard: strategies above manipulativeness threshold 7 are suppressed until sufficient feedback is collected.

---

## 🧪 Celery Background Jobs

| Task | Schedule | Purpose |
|---|---|---|
| `take_monitoring_snapshot` | Every 15 min | Capture system-wide metrics |
| `refresh_all_embeddings` | Every 6h | Recompute behavioral vectors |
| `check_and_retrain` | Every 12h | Evaluate + update active policy |
| `analyze_running_experiments` | Every 3h | Auto-analyze A/B tests |
| `detect_and_flag_failures` | On demand | Scan bandit arms for failure modes |

---

## 🛠️ Tech Stack

**Backend:** FastAPI · SQLAlchemy (async) · PostgreSQL · Redis · Celery · NumPy · SciPy · scikit-learn · Prometheus · structlog · passlib

**Frontend:** React 18 · Vite · React Router · Zustand · Recharts · Lucide · date-fns

**ML:** Thompson Sampling · UCB1 · ε-Greedy · Contextual LinUCB · Beta-Bernoulli conjugate updates · two-sample t-test · Cohen's d

**Infrastructure:** Render · Netlify · PWA (Web App Manifest + Service Worker)

---

## 👩‍💻 Built by

**Swathi Gudivada** — [GitHub](https://github.com/swathi-2406) · [LinkedIn](https://linkedin.com/in/swathi-gudivada)

*Open to AI Engineer, MLOps Engineer, and Full-Stack roles.*
