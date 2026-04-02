"""
Celery application — background tasks for NudgeOps.
Tasks: retraining pipeline, monitoring snapshots, embedding refresh, experiment analysis.
"""
import asyncio
import json
from datetime import datetime
from celery import Celery
from celery.schedules import crontab
from core.config import settings

celery_app = Celery(
    "nudgeops",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["tasks.celery_app"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "monitoring-snapshot": {
            "task": "tasks.celery_app.take_monitoring_snapshot",
            "schedule": crontab(minute="*/15"),
        },
        "refresh-embeddings": {
            "task": "tasks.celery_app.refresh_all_embeddings",
            "schedule": crontab(hour="*/6"),
        },
        "check-retraining": {
            "task": "tasks.celery_app.check_and_retrain",
            "schedule": crontab(hour="*/12"),
        },
        "run-experiment-analysis": {
            "task": "tasks.celery_app.analyze_running_experiments",
            "schedule": crontab(hour="*/3"),
        },
    },
)


def run_async(coro):
    """Run an async coroutine from a sync Celery task."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(name="tasks.celery_app.take_monitoring_snapshot", bind=True, max_retries=3)
def take_monitoring_snapshot(self):
    """Capture system-wide monitoring metrics and store snapshot."""
    async def _run():
        from db.database import AsyncSessionLocal
        from db.models import MonitoringSnapshot
        from services.monitoring_service import compute_system_metrics, fairness_report
        async with AsyncSessionLocal() as db:
            metrics = await compute_system_metrics(db)
            fairness = await fairness_report(db)
            snapshot = MonitoringSnapshot(
                snapshot_type="system_metrics",
                metrics=json.dumps({**metrics, "fairness": fairness}),
                alerts=json.dumps(metrics.get("alerts", [])),
            )
            db.add(snapshot)
            await db.commit()
            return {"status": "ok", "alerts": len(metrics.get("alerts", []))}
    try:
        return run_async(_run())
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(name="tasks.celery_app.refresh_all_embeddings", bind=True)
def refresh_all_embeddings(self):
    """Recompute behavioral embeddings for all active users."""
    async def _run():
        from db.database import AsyncSessionLocal
        from db.models import User
        from sqlalchemy import select
        from ml.embeddings.user_embeddings import compute_and_store_embedding
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(User.id).where(User.is_active == True))
            user_ids = [r[0] for r in result.all()]
            refreshed = 0
            for uid in user_ids:
                try:
                    await compute_and_store_embedding(uid, db)
                    refreshed += 1
                except Exception:
                    pass
            return {"refreshed": refreshed, "total": len(user_ids)}
    return run_async(_run())


@celery_app.task(name="tasks.celery_app.check_and_retrain", bind=True)
def check_and_retrain(self):
    """Check if retraining is needed and trigger if so."""
    async def _run():
        from db.database import AsyncSessionLocal
        from db.models import Policy
        from ml.evaluation.policy_evaluator import check_for_retraining_needed, evaluate_policy
        from sqlalchemy import select
        import json as _json
        async with AsyncSessionLocal() as db:
            should_retrain, reason = await check_for_retraining_needed(db)
            if not should_retrain:
                return {"retrained": False, "reason": reason}

            # Evaluate current active policy
            active = await db.execute(select(Policy).where(Policy.status == "active").limit(1))
            policy = active.scalar_one_or_none()
            if policy:
                metrics = await evaluate_policy(policy.id, db)
                policy.performance_metrics = _json.dumps(metrics)
                await db.commit()
                return {"retrained": True, "reason": reason, "metrics": metrics}
            return {"retrained": False, "reason": "no active policy"}
    return run_async(_run())


@celery_app.task(name="tasks.celery_app.analyze_running_experiments", bind=True)
def analyze_running_experiments(self):
    """Run statistical analysis on all running experiments."""
    async def _run():
        from db.database import AsyncSessionLocal
        from db.models import Experiment
        from ml.evaluation.policy_evaluator import run_ab_test_analysis
        from sqlalchemy import select
        import json as _json
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Experiment).where(Experiment.status == "running"))
            experiments = result.scalars().all()
            updates = []
            for exp in experiments:
                analysis = await run_ab_test_analysis(
                    exp.control_policy_id, exp.treatment_policy_id, db
                )
                exp.results = _json.dumps(analysis)
                if analysis.get("status") == "complete" and analysis.get("significant"):
                    exp.winner = analysis.get("winner")
                updates.append({"experiment_id": exp.id, "status": analysis.get("status")})
            await db.commit()
            return {"analyzed": len(updates), "experiments": updates}
    return run_async(_run())


@celery_app.task(name="tasks.celery_app.detect_and_flag_failures", bind=True)
def detect_and_flag_failures(self):
    """Scan all bandit states and flag failing intervention arms."""
    async def _run():
        from db.database import AsyncSessionLocal
        from db.models import BanditState
        from sqlalchemy import select
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(BanditState))
            states = result.scalars().all()
            flagged = 0
            for state in states:
                recent = state.get_recent_rewards()
                if len(recent) >= 10:
                    avg = sum(recent[-10:]) / 10
                    was_failing = state.is_failing
                    state.is_failing = avg < -0.1
                    if state.is_failing and not was_failing:
                        flagged += 1
            await db.commit()
            return {"flagged_new_failures": flagged, "total_states": len(states)}
    return run_async(_run())
