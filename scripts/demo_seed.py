#!/usr/bin/env python3
"""
Demo data seeder — creates sample users, events and intervention feedback.
Safe to run multiple times (skips existing data).

Run: python scripts/demo_seed.py
"""
import asyncio, random, sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from datetime import datetime, timedelta
from db.database import engine, Base, AsyncSessionLocal
from db.models import User, UserEvent, InterventionLog, BanditState, Intervention, Policy
from sqlalchemy import select

SEGMENTS = ["new_user", "moderate_engagement", "high_engagement", "at_risk_churn", "returning"]
EVENT_TYPES = ["session_start", "session_end", "task_complete", "goal_update", "profile_view", "notification_open"]
FEEDBACK_SIGNALS = ["completed", "engaged", "ignored", "dismissed", "negative"]
FEEDBACK_WEIGHTS = [0.25, 0.30, 0.25, 0.12, 0.08]
REWARD_MAP = {"completed": 1.0, "engaged": 0.5, "ignored": 0.0, "dismissed": -0.2, "negative": -0.5}

SAMPLE_USERS = [
    {"external_id": "usr_001", "display_name": "Alex Chen",    "segment": "high_engagement"},
    {"external_id": "usr_002", "display_name": "Jordan Lee",   "segment": "moderate_engagement"},
    {"external_id": "usr_003", "display_name": "Sam Patel",    "segment": "at_risk_churn"},
    {"external_id": "usr_004", "display_name": "Morgan Wu",    "segment": "new_user"},
    {"external_id": "usr_005", "display_name": "Casey Kim",    "segment": "returning"},
    {"external_id": "usr_006", "display_name": "Riley Singh",  "segment": "high_engagement"},
    {"external_id": "usr_007", "display_name": "Drew Nair",    "segment": "moderate_engagement"},
    {"external_id": "usr_008", "display_name": "Avery Osei",   "segment": "at_risk_churn"},
]


async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    from db.seed import seed_initial_data
    await seed_initial_data()

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Intervention))
        interventions = result.scalars().all()

        policy_result = await db.execute(select(Policy).where(Policy.status == "active").limit(1))
        policy = policy_result.scalar_one_or_none()

        now = datetime.utcnow()
        created_users = []

        # Create users (skip if already exist)
        for u_data in SAMPLE_USERS:
            existing = await db.execute(select(User).where(User.external_id == u_data["external_id"]))
            user = existing.scalar_one_or_none()
            if not user:
                user = User(
                    external_id=u_data["external_id"],
                    display_name=u_data["display_name"],
                    segment=u_data["segment"],
                    email=f"{u_data['external_id']}@demo.nudgeops.io"
                )
                db.add(user)
                await db.flush()
                print(f"  + Created user: {u_data['display_name']}")
            else:
                print(f"  ~ Skipped existing user: {u_data['display_name']}")
            created_users.append(user)

        await db.commit()

        # Add events + bandit states + logs for each user
        for user in created_users:
            # Events — always add fresh ones (they accumulate naturally)
            n_events = random.randint(10, 80) if user.segment != "at_risk_churn" else random.randint(1, 10)
            for _ in range(n_events):
                days_ago = random.uniform(0, 28)
                db.add(UserEvent(
                    user_id=user.id,
                    event_type=random.choice(EVENT_TYPES),
                    event_source="app",
                    properties=json.dumps({"demo": True}),
                    created_at=now - timedelta(days=days_ago),
                ))

            # Bandit states — only insert for types not yet present
            existing_states = await db.execute(
                select(BanditState.intervention_type).where(BanditState.user_id == user.id)
            )
            existing_types = {r[0] for r in existing_states.all()}

            for intv in interventions:
                if intv.intervention_type in existing_types:
                    continue
                n_pulls = random.randint(0, 15)
                total_reward = sum(random.uniform(-0.5, 1.0) for _ in range(n_pulls))
                mean_reward = total_reward / n_pulls if n_pulls else 0.0
                alpha = 1.0 + max(0, total_reward)
                beta = 1.0 + max(0, n_pulls - max(0, total_reward))
                db.add(BanditState(
                    user_id=user.id,
                    intervention_type=intv.intervention_type,
                    alpha=alpha, beta=beta,
                    n_pulls=n_pulls, total_reward=total_reward, mean_reward=mean_reward,
                    recent_rewards=json.dumps([random.uniform(-0.5, 1.0) for _ in range(min(n_pulls, 10))]),
                ))

            # Intervention logs
            n_logs = random.randint(3, 20)
            for _ in range(n_logs):
                intv = random.choice(interventions)
                days_ago = random.uniform(0, 28)
                signal = random.choices(FEEDBACK_SIGNALS, weights=FEEDBACK_WEIGHTS, k=1)[0]
                db.add(InterventionLog(
                    user_id=user.id,
                    intervention_id=intv.id,
                    policy_id=policy.id if policy else None,
                    bandit_strategy="thompson_sampling",
                    context_features=json.dumps({}),
                    feedback_signal=signal,
                    reward=REWARD_MAP[signal],
                    feedback_at=now - timedelta(days=days_ago - 0.1),
                    delivered_at=now - timedelta(days=days_ago),
                    message_rendered=intv.message_template,
                ))

        await db.commit()
        print(f"\n✅ Demo data seeded: {len(created_users)} users ready.")
        print(f"   API:      http://localhost:8000")
        print(f"   Docs:     http://localhost:8000/docs")
        print(f"   Frontend: http://localhost:3000")


if __name__ == "__main__":
    asyncio.run(seed())
