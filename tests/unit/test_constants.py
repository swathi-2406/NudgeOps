"""Unit tests for constants and metadata."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../backend'))

from core.constants import (
    InterventionType, INTERVENTION_METADATA, FEEDBACK_REWARD, FeedbackSignal
)


def test_all_intervention_types_have_metadata():
    for itype in InterventionType:
        assert itype in INTERVENTION_METADATA, f"Missing metadata for {itype}"


def test_metadata_has_required_fields():
    required = ["display_name", "description", "risk_level", "manipulativeness_score", "example_message"]
    for itype, meta in INTERVENTION_METADATA.items():
        for field in required:
            assert field in meta, f"Missing {field} in {itype} metadata"


def test_manipulativeness_scores_in_range():
    for itype, meta in INTERVENTION_METADATA.items():
        score = meta["manipulativeness_score"]
        assert 1 <= score <= 10, f"{itype} score {score} out of range"


def test_all_feedback_signals_have_rewards():
    for signal in FeedbackSignal:
        assert signal in FEEDBACK_REWARD, f"Missing reward for {signal}"


def test_reward_range():
    for signal, reward in FEEDBACK_REWARD.items():
        assert -1.0 <= reward <= 1.0, f"Reward {reward} for {signal} out of [-1,1]"


def test_completed_has_highest_reward():
    assert FEEDBACK_REWARD[FeedbackSignal.COMPLETED] == max(FEEDBACK_REWARD.values())


def test_negative_has_lowest_reward():
    assert FEEDBACK_REWARD[FeedbackSignal.NEGATIVE] == min(FEEDBACK_REWARD.values())
