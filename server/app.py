"""
Rehabilitation Scheduler — FastAPI Server
Exposes all required OpenEnv + hackathon endpoints.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional

from openenv.core.env_server import create_fastapi_app
from server.rehab_environment import RehabEnvironment
from models import RehabAction, RehabObservation, ActionType, ProgramType


# ─────────────────────────────────────────────
# Core OpenEnv app (handles /ws /reset /step /state /health /web /docs)
# ─────────────────────────────────────────────

app = create_fastapi_app(RehabEnvironment, RehabAction, RehabObservation)


def _remove_route(path: str, method: str) -> None:
    """Remove an auto-generated route so custom handlers can own that path."""
    method = method.upper()
    app.router.routes = [
        route
        for route in app.router.routes
        if not (
            getattr(route, "path", None) == path
            and method in getattr(route, "methods", set())
        )
    ]


# Override OpenEnv default HTTP handlers with explicit stateful endpoints.
for _path, _method in [
    ("/health", "GET"),
    ("/reset", "POST"),
    ("/step", "POST"),
    ("/state", "GET"),
]:
    _remove_route(_path, _method)


# ─────────────────────────────────────────────
# Hackathon-required extra endpoints
# ─────────────────────────────────────────────

# Singleton environment for extra endpoints
_env = RehabEnvironment()


@app.get("/tasks")
async def list_tasks():
    """
    Returns all 3 tasks and the action schema.
    Required by hackathon pre-submission checklist.
    """
    return {
        "tasks": [
            {
                "task_id": 1,
                "name": "Basic Allocation",
                "difficulty": "easy",
                "description": (
                    "20 inmates, 25 program slots across 5 types. "
                    "No conflicts, no refusals. Assign programs to maximize "
                    "recidivism reduction."
                ),
                "max_steps": 40,
                "expected_score_range": "0.75 – 1.00",
            },
            {
                "task_id": 2,
                "name": "Constrained Scheduling",
                "difficulty": "medium",
                "description": (
                    "50 inmates, only 30 slots (60% capacity). "
                    "5 conflict pairs, 3 refusals, 2 high-risk dynamic arrivals. "
                    "Prioritize high-risk and respect all constraints."
                ),
                "max_steps": 80,
                "expected_score_range": "0.50 – 0.85",
            },
            {
                "task_id": 3,
                "name": "Crisis Reoptimization",
                "difficulty": "hard",
                "description": (
                    "200 inmates, dynamic arrivals every 5 steps. "
                    "Vocational training budget cut at step 10 — agent must "
                    "reassign all affected inmates live without restarting."
                ),
                "max_steps": 200,
                "expected_score_range": "0.30 – 0.70",
            },
        ],
        "action_schema": {
            "action_type": {
                "type": "string",
                "enum": [a.value for a in ActionType],
                "required": True,
                "description": "Type of action to perform",
            },
            "inmate_id": {
                "type": "string",
                "required": "for assign_program, reschedule, handle_dropout, escalate_case",
                "example": "I-003",
            },
            "program_type": {
                "type": "string",
                "enum": [p.value for p in ProgramType],
                "required": "for assign_program, reschedule",
            },
            "replacement_id": {
                "type": "string",
                "required": "for handle_dropout (optional — waitlist inmate to fill slot)",
            },
            "from_program": {
                "type": "string",
                "enum": [p.value for p in ProgramType],
                "required": "for reallocate_budget",
            },
            "to_program": {
                "type": "string",
                "enum": [p.value for p in ProgramType],
                "required": "for reallocate_budget",
            },
            "slots": {
                "type": "integer",
                "required": "for reallocate_budget",
                "description": "Number of slots to move between programs",
            },
        },
    }


class GraderRequest(BaseModel):
    task_id: int = 1
    seed:    int = 42


class ResetRequest(BaseModel):
    task_id: int = 1
    seed: int = 42


@app.post("/reset")
async def reset(request: ResetRequest):
    """Reset the singleton environment and return the initial observation."""
    return _env.reset(task_id=request.task_id, seed=request.seed)


@app.post("/step")
async def step(action: RehabAction):
    """Apply one action to the active episode and return updated observation."""
    return _env.step(action)


@app.get("/state")
async def state():
    """Expose episode-level metadata for the active singleton environment."""
    return _env.state


@app.post("/grader")
async def run_grader(request: GraderRequest):
    """
    Runs a complete random-policy episode and returns the grader score.
    Required by hackathon pre-submission checklist.
    """
    import random as _random

    env = RehabEnvironment()
    obs = env.reset(task_id=request.task_id, seed=request.seed)

    rng = _random.Random(request.seed + 999)
    steps = 0

    while not obs.done and steps < 300:
        steps += 1
        # Simple greedy heuristic for grader demo
        unassigned = [
            i for i in obs.inmates
            if i["assigned_program"] is None
        ]
        slots_available = {
            k: v for k, v in obs.program_slots.items() if v > 0
        }

        if unassigned and slots_available:
            inmate = sorted(unassigned, key=lambda x: -x["risk_score"])[0]
            program = list(slots_available.keys())[0]
            action = RehabAction(
                action_type=ActionType.ASSIGN_PROGRAM,
                inmate_id=inmate["inmate_id"],
                program_type=ProgramType(program),
            )
        else:
            action = RehabAction(action_type=ActionType.SUBMIT_SCHEDULE)

        obs = env.step(action)

    if not obs.done:
        obs = env.step(RehabAction(action_type=ActionType.SUBMIT_SCHEDULE))

    return {
        "task_id":      request.task_id,
        "seed":         request.seed,
        "grader_score": obs.reward,
        "steps_taken":  env.state.step_count,
        "violations":   env.state.total_violations,
        "assignments":  env.state.total_assignments,
        "final_avg_risk": env.state.current_avg_risk,
    }


@app.get("/baseline")
async def run_baseline():
    """
    Runs the greedy baseline agent on all 3 tasks.
    Returns reproducible scores for hackathon validation.
    Required by hackathon pre-submission checklist.
    """
    scores = {}
    for task_id in [1, 2, 3]:
        result = await run_grader(GraderRequest(task_id=task_id, seed=42))
        scores[f"task_{task_id}"] = result

    return {
        "baseline_agent": "greedy_priority",
        "description": "Assigns highest-risk unassigned inmate to first available slot each step",
        "scores": scores,
        "note": "Full OpenAI-based baseline in baseline_agent.py",
    }


@app.get("/health")
async def health():
    return {"status": "healthy", "environment": "rehab_scheduler", "version": "1.0.0"}
