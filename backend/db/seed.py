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


INTERVENTION_MESSAGES = {
    "streak_tracker": [
        "🔥 Day {streak} streak! Don't break the chain now.",
        "🔥 {streak} days strong! You're on fire.",
        "⚡ Your streak is alive. Keep it that way.",
        "🏆 {streak} days in a row. Legend behavior.",
    ],
    "dark_humor_reminder": [
        "⚰️ Reminder: you're not getting younger. Maybe do the thing today.",
        "💀 Future you is watching. Don't disappoint them.",
        "🪦 One day you'll wish you'd started today. That day is not today. Yet.",
        "😬 The only thing worse than doing it is explaining why you didn't.",
    ],
    "loss_framing": [
        "⚠️ You're losing 3 days of progress by skipping today.",
        "📉 Every day you skip, someone else gets ahead.",
        "⚠️ You've worked too hard to throw it away today.",
        "🔻 Skipping today costs you more than you think.",
    ],
    "positive_reinforcement": [
        "🌟 Amazing work! You completed 80% of your goal this week.",
        "✨ You're doing better than 90% of people who started with you.",
        "💚 Progress is progress, no matter how small. Keep going.",
        "🎉 Look how far you've come! Today is another win.",
    ],
    "micro_challenge": [
        "⚡ Today's challenge: just 5 minutes. That's it. Go.",
        "🎯 One small thing today. Just one. You got this.",
        "💪 Tiny actions compound. Do the smallest version right now.",
        "⚡ 5 minutes. Set a timer. Start now.",
    ],
    "social_proof": [
        "👥 1,247 people like you finished this task today.",
        "🌍 Most people in your position have already done this today.",
        "👥 Your peers are showing up. So can you.",
        "📊 People with your habits report feeling 40% better. Keep going.",
    ],
    "implementation_intention": [
        "📅 When you finish lunch today, you'll spend 10 mins on this.",
        "🗓️ Pick a specific time today and lock it in. When is it?",
        "📌 If-then plan: When I [trigger], I will do this habit.",
        "⏰ Schedule it like a meeting. What time works today?",
    ],
    "progress_visualization": [
        "📊 You're 68% to your goal! Just 3 more sessions to go.",
        "📈 Look at your heatmap — you're building something real.",
        "🎯 You're closer than you think. Check your progress.",
        "📊 Every completion fills in another square. Fill today's.",
    ],
    "commitment_device": [
        "🤝 You committed to doing this yesterday. Time to follow through.",
        "📋 You said you would. That still means something.",
        "🤝 Your future self made a deal with your present self. Honor it.",
        "💬 You told yourself you'd do this. Be someone who keeps promises.",
    ],
    "public_accountability": [
        "📢 Your network saw you commit to this. Let's not let them down.",
        "👀 People are watching your journey. Show them what you've got.",
        "📣 You made this public for a reason. Today is that reason.",
        "🌐 Your community is rooting for you. Don't go quiet now.",
    ],
}