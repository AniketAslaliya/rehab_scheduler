"""Deterministic baseline inference script for the Rehab Scheduler environment."""

from __future__ import annotations

import json
import os
from typing import Any

import httpx


ENV_BASE_URL = os.environ.get("REHAB_ENV_URL", "http://localhost:8000")
SEED = int(os.environ.get("REHAB_BASELINE_SEED", "42"))

PROGRAM_EFFECTIVENESS = {
    "education": 1.8,
    "therapy": 2.2,
    "vocational": 1.5,
    "substance_abuse": 2.5,
    "anger_mgmt": 2.0,
}

OFFENCE_PROGRAM_AFFINITY = {
    "drug": ["substance_abuse", "therapy"],
    "violent": ["anger_mgmt", "therapy"],
    "property": ["vocational", "education"],
    "fraud": ["education", "vocational"],
    "dui": ["substance_abuse", "anger_mgmt"],
}


class RehabEnvClient:
    """Tiny HTTP client used by the baseline script."""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.Client(timeout=30.0)

    def reset(self, task_id: int, seed: int) -> dict[str, Any]:
        response = self.client.post(
            f"{self.base_url}/reset",
            json={"task_id": task_id, "seed": seed},
        )
        response.raise_for_status()
        return response.json()

    def step(self, action: dict[str, Any]) -> dict[str, Any]:
        response = self.client.post(f"{self.base_url}/step", json=action)
        response.raise_for_status()
        return response.json()

    def state(self) -> dict[str, Any]:
        response = self.client.get(f"{self.base_url}/state")
        response.raise_for_status()
        return response.json()

    def close(self) -> None:
        self.client.close()


def _program_score(inmate: dict[str, Any], program: str) -> float:
    """Estimate the value of assigning an inmate to a given program."""
    score = PROGRAM_EFFECTIVENESS[program] * float(inmate["receptivity"])
    if program in OFFENCE_PROGRAM_AFFINITY.get(inmate["offence_category"], []):
        score *= 1.3
    return score


def _has_conflict(
    inmate: dict[str, Any],
    program: str,
    assigned_by_id: dict[str, dict[str, Any]],
) -> bool:
    """Return True when the inmate conflicts with anyone already in the program."""
    conflicts = set(inmate.get("conflict_with", []))
    if not conflicts:
        return False

    for other in assigned_by_id.values():
        if other.get("assigned_program") == program and other["inmate_id"] in conflicts:
            return True
    return False


def choose_action(obs: dict[str, Any]) -> dict[str, Any]:
    """Select the next deterministic greedy action for the current observation."""
    assigned_by_id = {inmate["inmate_id"]: inmate for inmate in obs.get("inmates", [])}
    unassigned = sorted(
        (inmate for inmate in obs.get("inmates", []) if inmate["assigned_program"] is None),
        key=lambda inmate: (-float(inmate["risk_score"]), inmate["inmate_id"]),
    )
    available_programs = {
        program: slots
        for program, slots in obs.get("program_slots", {}).items()
        if slots > 0
    }

    for inmate in unassigned:
        best_program = None
        best_score = -1.0
        refused_programs = set(inmate.get("refused_programs", []))

        for program in sorted(available_programs):
            if program in refused_programs:
                continue
            if _has_conflict(inmate, program, assigned_by_id):
                continue

            score = _program_score(inmate, program)
            if score > best_score:
                best_score = score
                best_program = program

        if best_program is not None:
            return {
                "action_type": "assign_program",
                "inmate_id": inmate["inmate_id"],
                "program_type": best_program,
            }

    return {"action_type": "submit_schedule"}


def run_task(task_id: int, verbose: bool = True) -> dict[str, Any]:
    """Run one full episode and return the final metrics."""
    env = RehabEnvClient(ENV_BASE_URL)

    print(f"\n{'=' * 60}")
    print(f"Task {task_id} - starting deterministic baseline (seed={SEED})")
    print(f"{'=' * 60}")

    obs = env.reset(task_id=task_id, seed=SEED)
    step_count = 0
    final_reward = 0.0

    while not obs.get("done", False):
        step_count += 1
        action = choose_action(obs)

        if verbose:
            print(f"Step {step_count:3d}: {action}")

        obs = env.step(action)
        if obs.get("reward") is not None:
            final_reward = obs["reward"]

        if action["action_type"] == "submit_schedule":
            break

    state = env.state()
    env.close()

    result = {
        "task_id": task_id,
        "seed": SEED,
        "baseline_agent": "deterministic_greedy_affinity",
        "steps_taken": step_count,
        "final_score": final_reward,
        "total_assignments": state.get("total_assignments"),
        "total_violations": state.get("total_violations"),
        "current_avg_risk": state.get("current_avg_risk"),
        "initial_avg_risk": state.get("initial_avg_risk"),
    }

    print(f"\nTask {task_id} complete:")
    print(f"  Score:       {final_reward:.4f}")
    print(f"  Assignments: {state.get('total_assignments')}")
    print(f"  Violations:  {state.get('total_violations')}")
    print(f"  Risk:        {state.get('initial_avg_risk'):.2f} -> {state.get('current_avg_risk'):.2f}")

    return result


def main() -> None:
    """Run the baseline across all tasks and persist the results to disk."""
    print("Rehabilitation Scheduler - Baseline Agent")
    print(f"Environment: {ENV_BASE_URL}")
    print("Strategy:    deterministic_greedy_affinity")

    all_results: dict[str, Any] = {}
    for task_id in [1, 2, 3]:
        try:
            all_results[f"task_{task_id}"] = run_task(task_id)
        except Exception as exc:  # pragma: no cover - surfaced to user
            print(f"Task {task_id} failed: {exc}")
            all_results[f"task_{task_id}"] = {"error": str(exc)}

    print(f"\n{'=' * 60}")
    print("BASELINE RESULTS SUMMARY")
    print(f"{'=' * 60}")
    for task_name, result in all_results.items():
        print(f"  {task_name}: {result.get('final_score', 'error')}")

    with open("baseline_results.json", "w", encoding="utf-8") as file:
        json.dump(all_results, file, indent=2)
    print("\nResults saved to baseline_results.json")


if __name__ == "__main__":
    main()
