"""
Core constants for NudgeOps.
Defines all intervention types, their properties, and system-level enums.
"""

from enum import Enum
from typing import Dict, Any


class InterventionType(str, Enum):
    """All available intervention / motivational strategy types."""
    STREAK_TRACKER = "streak_tracker"           # Gamified streak counting
    PUBLIC_ACCOUNTABILITY = "public_accountability"  # Social sharing / public goal
    DARK_HUMOR_REMINDER = "dark_humor_reminder"   # Funny, slightly dark reminders
    LOSS_FRAMING = "loss_framing"               # Loss aversion framing
    POSITIVE_REINFORCEMENT = "positive_reinforcement"  # Praise and rewards
    SOCIAL_PROOF = "social_proof"               # Others are doing it
    IMPLEMENTATION_INTENTION = "implementation_intention"  # If-then planning
    PROGRESS_VISUALIZATION = "progress_visualization"    # Visual progress bar/chart
    COMMITMENT_DEVICE = "commitment_device"         # Lock-in commitments
    MICRO_CHALLENGE = "micro_challenge"           # Small, achievable daily challenges


class BanditStrategy(str, Enum):
    """Multi-armed bandit exploration strategies."""
    EPSILON_GREEDY = "epsilon_greedy"
    UCB = "ucb"                  # Upper Confidence Bound
    THOMPSON_SAMPLING = "thompson_sampling"
    CONTEXTUAL_LINUCB = "contextual_linucb"     # Contextual bandit


class PolicyStatus(str, Enum):
    """Policy lifecycle states."""
    DRAFT = "draft"
    ACTIVE = "active"
    SHADOW = "shadow"        # Running silently for evaluation
    RETIRED = "retired"
    ROLLED_BACK = "rolled_back"


class ExperimentStatus(str, Enum):
    """A/B test lifecycle states."""
    CREATED = "created"
    RUNNING = "running"
    PAUSED = "paused"
    CONCLUDED = "concluded"
    ABORTED = "aborted"


class FeedbackSignal(str, Enum):
    """User response signals to an intervention."""
    ENGAGED = "engaged"          # Clicked / opened
    COMPLETED = "completed"      # Finished the target behavior
    IGNORED = "ignored"          # Shown but no action
    DISMISSED = "dismissed"      # Explicitly dismissed
    NEGATIVE = "negative"        # Negative reaction / opted out


class UserSegment(str, Enum):
    """Behavioral user segments."""
    HIGH_ENGAGEMENT = "high_engagement"
    MODERATE_ENGAGEMENT = "moderate_engagement"
    LOW_ENGAGEMENT = "low_engagement"
    AT_RISK_CHURN = "at_risk_churn"
    NEW_USER = "new_user"
    RETURNING = "returning"


# Intervention metadata: display name, description, risk level
INTERVENTION_METADATA: Dict[InterventionType, Dict[str, Any]] = {
    InterventionType.STREAK_TRACKER: {
        "display_name": "Streak Tracker",
        "description": "Motivate with gamified daily streaks and milestone badges.",
        "risk_level": "low",
        "manipulativeness_score": 2,  # 1-10, higher = more manipulative
        "example_message": "🔥 Day 7 streak! Don't break the chain now.",
    },
    InterventionType.PUBLIC_ACCOUNTABILITY: {
        "display_name": "Public Accountability",
        "description": "Share goals publicly to harness social commitment.",
        "risk_level": "medium",
        "manipulativeness_score": 4,
        "example_message": "📢 Your network saw you commit to this. Let's not let them down.",
    },
    InterventionType.DARK_HUMOR_REMINDER: {
        "display_name": "Dark Humor Reminder",
        "description": "Funny, slightly morbid reminders that cut through noise.",
        "risk_level": "low",
        "manipulativeness_score": 2,
        "example_message": "⚰️ Reminder: you're not getting younger. Maybe do the thing today.",
    },
    InterventionType.LOSS_FRAMING: {
        "display_name": "Loss Framing",
        "description": "Frame inaction as losing something valuable.",
        "risk_level": "high",
        "manipulativeness_score": 7,
        "example_message": "⚠️ You're losing 3 days of progress by skipping today.",
    },
    InterventionType.POSITIVE_REINFORCEMENT: {
        "display_name": "Positive Reinforcement",
        "description": "Celebrate wins and progress with genuine praise.",
        "risk_level": "low",
        "manipulativeness_score": 1,
        "example_message": "🌟 Amazing work! You completed 80% of your goal this week.",
    },
    InterventionType.SOCIAL_PROOF: {
        "display_name": "Social Proof",
        "description": "Show that peers are achieving similar goals.",
        "risk_level": "medium",
        "manipulativeness_score": 5,
        "example_message": "👥 1,247 people like you finished this task today.",
    },
    InterventionType.IMPLEMENTATION_INTENTION: {
        "display_name": "Implementation Intention",
        "description": "If-then planning to remove friction from behavior.",
        "risk_level": "low",
        "manipulativeness_score": 2,
        "example_message": "📅 When you finish lunch today, you'll spend 10 mins on this.",
    },
    InterventionType.PROGRESS_VISUALIZATION: {
        "display_name": "Progress Visualization",
        "description": "Visual progress indicators showing how far you've come.",
        "risk_level": "low",
        "manipulativeness_score": 1,
        "example_message": "📊 You're 68% to your goal! Just 3 more sessions to go.",
    },
    InterventionType.COMMITMENT_DEVICE: {
        "display_name": "Commitment Device",
        "description": "Pre-commit to behavior to leverage self-binding.",
        "risk_level": "medium",
        "manipulativeness_score": 5,
        "example_message": "🤝 You committed to doing this yesterday. Time to follow through.",
    },
    InterventionType.MICRO_CHALLENGE: {
        "display_name": "Micro Challenge",
        "description": "Break down goals into tiny, winnable daily challenges.",
        "risk_level": "low",
        "manipulativeness_score": 2,
        "example_message": "⚡ Today's challenge: just 5 minutes. That's it. Go.",
    },
}

# Reward signal weights for bandit feedback
FEEDBACK_REWARD: Dict[FeedbackSignal, float] = {
    FeedbackSignal.COMPLETED: 1.0,
    FeedbackSignal.ENGAGED: 0.5,
    FeedbackSignal.IGNORED: 0.0,
    FeedbackSignal.DISMISSED: -0.2,
    FeedbackSignal.NEGATIVE: -0.5,
}
