"""Unit tests for the bandit engine."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../backend'))

import pytest
import numpy as np
from ml.bandit.engine import ArmState, BanditEngine, initialize_fresh_arms
from core.constants import BanditStrategy, InterventionType


def make_engine(strategy=BanditStrategy.THOMPSON_SAMPLING):
    arms = initialize_fresh_arms()
    return BanditEngine(
        user_id="test_user",
        arm_states=arms,
        strategy=strategy,
    )


class TestArmState:
    def test_initial_state(self):
        arm = ArmState("streak_tracker")
        assert arm.alpha == 1.0
        assert arm.beta == 1.0
        assert arm.n_pulls == 0
        assert arm.mean_reward == 0.0

    def test_update_positive_reward(self):
        arm = ArmState("streak_tracker")
        arm.update(1.0)
        assert arm.n_pulls == 1
        assert arm.total_reward == 1.0
        assert arm.mean_reward == 1.0
        assert arm.alpha > 1.0  # increased by positive reward

    def test_update_negative_reward(self):
        arm = ArmState("streak_tracker")
        arm.update(-0.5)
        assert arm.n_pulls == 1
        assert arm.beta > 1.0  # increased by negative reward

    def test_recent_rewards_window(self):
        arm = ArmState("streak_tracker")
        for i in range(25):
            arm.update(0.5, window_size=20)
        assert len(arm.recent_rewards) == 20  # capped at window

    def test_thompson_sample_returns_float(self):
        arm = ArmState("streak_tracker")
        sample = arm.thompson_sample()
        assert 0.0 <= sample <= 1.0


class TestBanditEngine:
    def test_select_arm_returns_valid_type(self):
        engine = make_engine()
        selected, reason = engine.select_arm()
        valid_types = [t.value for t in InterventionType]
        assert selected in valid_types
        assert isinstance(reason, str)

    def test_epsilon_greedy_selection(self):
        engine = make_engine(BanditStrategy.EPSILON_GREEDY)
        selected, _ = engine.select_arm()
        assert selected in [t.value for t in InterventionType]

    def test_ucb_selection(self):
        engine = make_engine(BanditStrategy.UCB)
        selected, reason = engine.select_arm()
        assert selected in [t.value for t in InterventionType]
        assert "ucb" in reason or "explore" in reason

    def test_thompson_prefers_better_arm_after_updates(self):
        arms = initialize_fresh_arms()
        # Give streak_tracker very high rewards
        for _ in range(30):
            arms[InterventionType.STREAK_TRACKER.value].update(1.0)
        # Give loss_framing very low rewards
        for _ in range(30):
            arms[InterventionType.LOSS_FRAMING.value].update(-0.5)

        engine = BanditEngine("test_user", arms, BanditStrategy.THOMPSON_SAMPLING)
        counts = {}
        for _ in range(100):
            selected, _ = engine.select_arm()
            counts[selected] = counts.get(selected, 0) + 1

        # streak_tracker should win majority of the time
        assert counts.get(InterventionType.STREAK_TRACKER.value, 0) > 40

    def test_excluded_arms_not_selected(self):
        arms = initialize_fresh_arms()
        engine = BanditEngine(
            "test_user", arms, BanditStrategy.EPSILON_GREEDY,
            excluded_types=[InterventionType.LOSS_FRAMING.value]
        )
        for _ in range(50):
            selected, _ = engine.select_arm()
            assert selected != InterventionType.LOSS_FRAMING.value

    def test_failure_detection(self):
        engine = make_engine()
        arm = engine.arms[InterventionType.LOSS_FRAMING.value]
        for _ in range(15):
            arm.update(-0.5)
        failing = engine.detect_failures(window=10, threshold=-0.1)
        assert InterventionType.LOSS_FRAMING.value in failing
        assert arm.is_failing

    def test_fairness_distribution_sums_to_one(self):
        arms = initialize_fresh_arms()
        for arm in arms.values():
            arm.n_pulls = 10
        engine = BanditEngine("test_user", arms)
        dist = engine.get_fairness_distribution()
        assert abs(sum(dist.values()) - 1.0) < 0.001

    def test_fairness_violation_detected(self):
        arms = initialize_fresh_arms()
        # One arm has 80% of pulls
        arms[InterventionType.STREAK_TRACKER.value].n_pulls = 80
        for k in arms:
            if k != InterventionType.STREAK_TRACKER.value:
                arms[k].n_pulls = 2
        engine = BanditEngine("test_user", arms)
        violation = engine.check_fairness_violation()
        assert violation == InterventionType.STREAK_TRACKER.value

    def test_contextual_linucb_fallback(self):
        engine = make_engine(BanditStrategy.CONTEXTUAL_LINUCB)
        # No context → should fall back to Thompson
        selected, reason = engine.select_arm(context=None)
        assert selected in [t.value for t in InterventionType]

    def test_contextual_linucb_with_context(self):
        engine = make_engine(BanditStrategy.CONTEXTUAL_LINUCB)
        context = np.random.rand(10).astype(np.float32)
        selected, reason = engine.select_arm(context=context)
        assert selected in [t.value for t in InterventionType]
        assert reason == "contextual_linucb"


class TestInitializeFreshArms:
    def test_all_intervention_types_present(self):
        arms = initialize_fresh_arms()
        for itype in InterventionType:
            assert itype.value in arms

    def test_all_start_at_prior(self):
        arms = initialize_fresh_arms()
        for arm in arms.values():
            assert arm.alpha == 1.0
            assert arm.beta == 1.0
            assert arm.n_pulls == 0
