# NudgeOps Architecture

## System Overview

```
                         ┌─────────────────────────────────────────┐
                         │           NudgeOps Platform              │
                         │                                          │
  User App  ──events──►  │  FastAPI Backend                         │
            ◄─nudge───   │  ├── Event Ingestion Pipeline            │
                         │  ├── Feature Store (SQLite + Redis)      │
                         │  ├── Bandit Engine                       │
                         │  │   ├── Thompson Sampling               │
                         │  │   ├── UCB1                            │
                         │  │   ├── ε-Greedy                        │
                         │  │   └── Contextual LinUCB               │
                         │  ├── Policy Registry                     │
                         │  ├── A/B Testing Framework               │
                         │  ├── Monitoring + Fairness               │
                         │  └── Audit Logging                       │
                         │                                          │
                         │  Celery Workers (background)             │
                         │  ├── Retraining Pipeline                 │
                         │  ├── Embedding Refresh                   │
                         │  ├── Monitoring Snapshots                │
                         │  └── Experiment Analysis                 │
                         └─────────────────────────────────────────┘
                                         │
                              ┌──────────┴──────────┐
                         SQLite DB             Redis Cache
                         (persistent)          (feature TTL)
```

## Bandit Learning Loop

```
1. User triggers nudge request
        │
        ▼
2. Load user's bandit arm states from DB
        │
        ▼
3. Compute user features (cached in Redis)
   ├── engagement metrics
   ├── recency / consistency
   └── intervention history
        │
        ▼
4. Select arm via bandit strategy
   ├── Thompson: sample Beta(α,β) per arm → pick max
   ├── UCB: score = μ + √(log N / n) → pick max
   ├── ε-Greedy: explore random (15%) or exploit best (85%)
   └── Contextual LinUCB: Thompson + context vector boost
        │
        ▼
5. Deliver intervention → log to DB
        │
        ▼
6. User responds (or ignores) → feedback signal
        │
        ▼
7. Compute reward: completed=1.0, engaged=0.5,
                   ignored=0.0, dismissed=-0.2, negative=-0.5
        │
        ▼
8. Update arm: α += reward_clamped, β += (1 - reward_clamped)
        │
        ▼
9. Check for arm failure (rolling window avg < -0.1)
10. Check fairness (no arm > 60% of total pulls)
```

## Policy Lifecycle

```
DRAFT → promote → ACTIVE → rollback → ROLLED_BACK
                     │
                   retire
                     │
                  RETIRED

SHADOW: runs silently for evaluation, no effect on users
```

## A/B Testing Flow

```
1. Create experiment (control_policy vs treatment_policy)
2. Start experiment (status: running)
3. Users assigned to arms via traffic_split hash
4. Both policies log interventions independently
5. Conclude: run two-sample t-test on reward distributions
   ├── p < 0.05 → statistically significant
   ├── winner = treatment if treatment_mean > control_mean
   └── else → inconclusive
6. Optionally promote winning policy
```

## Feature Store

Features computed per user over a 30-day rolling window:
- `activity_score`: normalized event count [0,1]
- `recency_score`: how recently the user was active [0,1]  
- `consistency_score`: session regularity [0,1]
- `engagement_rate`: (completed + engaged) / total deliveries
- `completion_rate`: completed / total deliveries
- `dismiss_rate`: dismissed / total deliveries
- `negative_rate`: negative / total deliveries
- `best_arm`: current highest-estimated intervention type
- `best_arm_reward`: mean reward of best arm

Features cached in Redis (TTL: 1h) and persisted in SQLite.
Invalidated on every new event ingestion.
