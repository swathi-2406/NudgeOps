"""Seed initial data: interventions, default policy."""
import structlog
from sqlalchemy import select
from db.database import AsyncSessionLocal
from db.models import Intervention, Policy
from core.constants import INTERVENTION_METADATA, InterventionType, PolicyStatus, BanditStrategy

logger = structlog.get_logger(__name__)

async def seed_initial_data():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Intervention).limit(1))
        if result.scalar_one_or_none() is None:
            interventions = []
            for itype, meta in INTERVENTION_METADATA.items():
                interventions.append(Intervention(
                    intervention_type=itype.value,
                    name=meta["display_name"],
                    description=meta["description"],
                    message_template=meta["example_message"],
                    channel="in_app",
                    manipulativeness_score=meta["manipulativeness_score"],
                    risk_level=meta["risk_level"],
                ))
            session.add_all(interventions)
            logger.info("seeded_interventions", count=len(interventions))

        result = await session.execute(select(Policy).where(Policy.name == "default_thompson"))
        if result.scalar_one_or_none() is None:
            import json
            policy = Policy(
                name="default_thompson",
                version="1.0.0",
                description="Default Thompson Sampling policy for all users",
                status=PolicyStatus.ACTIVE.value,
                bandit_strategy=BanditStrategy.THOMPSON_SAMPLING.value,
                config=json.dumps({
                    "prior_alpha": 1.0,
                    "prior_beta": 1.0,
                    "max_manipulativeness_score": 7,
                    "fairness_cap": 0.60,
                }),
                performance_metrics=json.dumps({}),
                created_by="system",
            )
            session.add(policy)
            logger.info("seeded_default_policy")

        await session.commit()
