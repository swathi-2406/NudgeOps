"""
NudgeOps Bandit Engine — Thompson Sampling, UCB, Epsilon-Greedy, Contextual LinUCB.
"""
import math, random
import numpy as np
from typing import Dict, List, Optional, Tuple
from core.constants import InterventionType, BanditStrategy, INTERVENTION_METADATA
from core.config import settings


class ArmState:
    def __init__(self, intervention_type: str):
        self.intervention_type = intervention_type
        self.alpha: float = settings.BANDIT_THOMPSON_PRIOR_ALPHA
        self.beta: float = settings.BANDIT_THOMPSON_PRIOR_BETA
        self.n_pulls: int = 0
        self.total_reward: float = 0.0
        self.mean_reward: float = 0.0
        self.recent_rewards: List[float] = []
        self.is_failing: bool = False

    def thompson_sample(self) -> float:
        return float(np.random.beta(self.alpha, self.beta))

    def update(self, reward: float, window_size: int = 20):
        self.n_pulls += 1
        self.total_reward += reward
        self.mean_reward = self.total_reward / self.n_pulls
        clamped = max(0.0, min(1.0, (reward + 1.0) / 2.0))
        self.alpha += clamped
        self.beta += (1.0 - clamped)
        self.recent_rewards.append(reward)
        if len(self.recent_rewards) > window_size:
            self.recent_rewards.pop(0)


class BanditEngine:
    def __init__(self, user_id: str, arm_states: Dict[str, ArmState],
                 strategy: BanditStrategy = BanditStrategy.THOMPSON_SAMPLING,
                 excluded_types: Optional[List[str]] = None, max_manipulativeness: int = 7):
        self.user_id = user_id
        self.arms = arm_states
        self.strategy = strategy
        self.excluded_types = set(excluded_types or [])
        self.max_manipulativeness = max_manipulativeness

    def _eligible_arms(self) -> Dict[str, ArmState]:
        eligible = {}
        for itype, arm in self.arms.items():
            if itype in self.excluded_types:
                continue
            try:
                meta = INTERVENTION_METADATA.get(InterventionType(itype), {})
            except ValueError:
                meta = {}
            if meta.get("manipulativeness_score", 0) > self.max_manipulativeness:
                continue
            if arm.is_failing and random.random() > 0.10:
                continue
            eligible[itype] = arm
        return eligible if eligible else self.arms

    def select_arm(self, context: Optional[np.ndarray] = None) -> Tuple[str, str]:
        eligible = self._eligible_arms()
        if self.strategy == BanditStrategy.EPSILON_GREEDY:
            return self._epsilon_greedy(eligible)
        elif self.strategy == BanditStrategy.UCB:
            return self._ucb(eligible)
        elif self.strategy == BanditStrategy.CONTEXTUAL_LINUCB:
            return self._contextual_linucb(eligible, context)
        return self._thompson_sampling(eligible)

    def _epsilon_greedy(self, arms):
        if random.random() < settings.BANDIT_EPSILON:
            return random.choice(list(arms.keys())), "explore_random"
        best = max(arms.items(), key=lambda x: x[1].mean_reward)
        return best[0], "exploit_best_mean"

    def _ucb(self, arms):
        total_pulls = sum(a.n_pulls for a in arms.values())
        scores = {}
        for itype, arm in arms.items():
            if arm.n_pulls == 0:
                scores[itype] = float("inf")
            else:
                scores[itype] = arm.mean_reward + settings.BANDIT_UCB_ALPHA * math.sqrt(
                    math.log(max(total_pulls, 1)) / arm.n_pulls)
        chosen = max(scores, key=scores.__getitem__)
        return chosen, "explore_ucb" if scores[chosen] == float("inf") else "ucb_score"

    def _thompson_sampling(self, arms):
        samples = {itype: arm.thompson_sample() for itype, arm in arms.items()}
        chosen = max(samples, key=samples.__getitem__)
        total_pulls = sum(a.n_pulls for a in arms.values())
        return chosen, "explore_thompson" if total_pulls < settings.MIN_SAMPLES_FOR_EXPLOITATION else "thompson_exploit"

    def _contextual_linucb(self, arms, context):
        if context is None or len(context) == 0:
            return self._thompson_sampling(arms)
        samples = {}
        arm_keys = list(self.arms.keys())
        for itype, arm in arms.items():
            base = arm.thompson_sample()
            idx = arm_keys.index(itype)
            boost = float(context[idx]) * 0.1 if idx < len(context) else 0.0
            samples[itype] = base + boost
        return max(samples, key=samples.__getitem__), "contextual_linucb"

    def detect_failures(self, window: int = 10, threshold: float = -0.1) -> List[str]:
        failing = []
        for itype, arm in self.arms.items():
            if len(arm.recent_rewards) >= window:
                avg = sum(arm.recent_rewards[-window:]) / window
                was_failing = arm.is_failing
                arm.is_failing = avg < threshold
                if arm.is_failing and not was_failing:
                    failing.append(itype)
        return failing

    def get_fairness_distribution(self) -> Dict[str, float]:
        total = sum(arm.n_pulls for arm in self.arms.values())
        if total == 0:
            return {k: 0.0 for k in self.arms}
        return {k: v.n_pulls / total for k, v in self.arms.items()}

    def check_fairness_violation(self) -> Optional[str]:
        for itype, share in self.get_fairness_distribution().items():
            if share > settings.MAX_SINGLE_INTERVENTION_SHARE:
                return itype
        return None


def arm_states_from_db(db_states) -> Dict[str, ArmState]:
    arms = {}
    for state in db_states:
        arm = ArmState(state.intervention_type)
        arm.alpha = state.alpha
        arm.beta = state.beta
        arm.n_pulls = state.n_pulls
        arm.total_reward = state.total_reward
        arm.mean_reward = state.mean_reward
        arm.recent_rewards = state.get_recent_rewards()
        arm.is_failing = state.is_failing
        arms[state.intervention_type] = arm
    return arms


def initialize_fresh_arms() -> Dict[str, ArmState]:
    return {itype.value: ArmState(itype.value) for itype in InterventionType}
