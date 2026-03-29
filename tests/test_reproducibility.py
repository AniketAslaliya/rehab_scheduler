"""Reproducibility tests - same seed must always produce same score."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import RehabAction, ActionType
from server.rehab_environment import RehabEnvironment


def run_full_episode(task_id: int, seed: int) -> float:
    """Run a complete episode and return final score."""
    env = RehabEnvironment()
    obs = env.reset(task_id=task_id, seed=seed)
    obs = env.step(RehabAction(action_type=ActionType.SUBMIT_SCHEDULE))
    return obs.reward


def test_same_seed_same_score():
    """Identical seed must produce identical score across 3 runs."""
    scores = [run_full_episode(task_id=1, seed=42) for _ in range(3)]
    assert scores[0] == scores[1] == scores[2], f"Scores differ across runs: {scores}"


def test_different_seeds_different_scores():
    """Different seeds must produce different case populations."""
    env_a = RehabEnvironment()
    env_b = RehabEnvironment()
    obs_42 = env_a.reset(task_id=1, seed=42)
    obs_99 = env_b.reset(task_id=1, seed=99)

    # Compare deterministic case features that should vary with different seeds.
    first_42 = obs_42.inmates[0]
    first_99 = obs_99.inmates[0]
    assert (
        first_42["risk_score"] != first_99["risk_score"]
        or first_42["offence_category"] != first_99["offence_category"]
        or obs_42.avg_risk_score != obs_99.avg_risk_score
    ), "Different seeds produced identical task profile"


def test_reproducibility_all_tasks():
    """All 3 tasks must be reproducible."""
    for task_id in [1, 2, 3]:
        s1 = run_full_episode(task_id=task_id, seed=42)
        s2 = run_full_episode(task_id=task_id, seed=42)
        assert s1 == s2, f"Task {task_id} not reproducible: {s1} != {s2}"
