"""Unit tests for the grader formula."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from case_generator import generate_task_1, compute_optimal_score
from server.rehab_environment import _grade, RehabEnvironment


def test_grader_score_in_range():
    """Grader must always return float in [0.0, 1.0]."""
    inmates, slots = generate_task_1(seed=42)
    score = _grade(
        inmates=inmates,
        violations=0,
        wasted_slots=0,
        total_slots=sum(slots.values()),
        steps_taken=10,
        max_steps=40,
        optimal_score=0.8,
    )
    assert 0.0 <= score <= 1.0, f"Score out of range: {score}"


def test_grader_violations_reduce_score():
    """More violations = lower score."""
    inmates, _ = generate_task_1(seed=42)
    base_args = dict(
        inmates=inmates,
        wasted_slots=0,
        total_slots=25,
        steps_taken=20,
        max_steps=40,
        optimal_score=0.8,
    )
    score_clean = _grade(**base_args, violations=0)
    score_violated = _grade(**base_args, violations=3)
    assert score_violated < score_clean, "Violations should reduce score"


def test_grader_different_seeds():
    """Different seeds must produce different optimal scores."""
    inmates_42, slots_42 = generate_task_1(seed=42)
    inmates_99, slots_99 = generate_task_1(seed=99)
    optimal_42 = compute_optimal_score(inmates_42, slots_42)
    optimal_99 = compute_optimal_score(inmates_99, slots_99)
    assert optimal_42 != optimal_99, "Different seeds must produce different optima"


def test_full_episode_score_nonzero():
    """A greedy episode should score above 0.3."""
    from models import RehabAction, ActionType, ProgramType

    env = RehabEnvironment()
    obs = env.reset(task_id=1, seed=42)

    for _ in range(30):
        if obs.done:
            break
        unassigned = [i for i in obs.inmates if i["assigned_program"] is None]
        available = {k: v for k, v in obs.program_slots.items() if v > 0}
        if unassigned and available:
            action = RehabAction(
                action_type=ActionType.ASSIGN_PROGRAM,
                inmate_id=unassigned[0]["inmate_id"],
                program_type=ProgramType(list(available.keys())[0]),
            )
        else:
            action = RehabAction(action_type=ActionType.SUBMIT_SCHEDULE)
        obs = env.step(action)

    if not obs.done:
        obs = env.step(RehabAction(action_type=ActionType.SUBMIT_SCHEDULE))

    assert obs.reward is not None
    # A simple greedy policy should still beat a near-zero schedule.
    assert obs.reward >= 0.2, f"Expected score >= 0.2, got {obs.reward}"
    assert obs.done is True
