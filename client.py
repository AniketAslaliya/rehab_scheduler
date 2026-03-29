"""
Rehabilitation Scheduler — Python Client
Import this in your training code or Colab notebooks.

Usage:
    from client import RehabEnv
    from models import RehabAction, ActionType, ProgramType

    with RehabEnv(base_url="https://YOUR_USERNAME-rehab-scheduler.hf.space").sync() as env:
        obs = env.reset(task_id=1, seed=42)
        obs = env.step(RehabAction(
            action_type=ActionType.ASSIGN_PROGRAM,
            inmate_id="I-001",
            program_type=ProgramType.THERAPY,
        ))
        print(obs.observation.avg_risk_score)
        state = env.state()
        print(state.grader_score)
"""

from openenv.core.env_client import EnvClient
from openenv.core.client_types import StepResult
from models import RehabAction, RehabObservation, RehabState


class RehabEnv(EnvClient[RehabAction, RehabObservation, RehabState]):
    """
    Typed client for the Rehabilitation Scheduler environment.
    Supports both sync (notebooks) and async (training loops).

    Sync usage:
        with RehabEnv(base_url="...").sync() as env:
            obs = env.reset(task_id=1)
            obs = env.step(RehabAction(...))

    Async usage:
        async with RehabEnv(base_url="...") as env:
            obs = await env.reset(task_id=1)
            obs = await env.step(RehabAction(...))
    """

    def _step_payload(self, action: RehabAction) -> dict:
        return action.model_dump(exclude_none=True)

    def _parse_result(self, payload: dict) -> StepResult:
        obs_data = payload.get("observation", payload)
        return StepResult(
            observation=RehabObservation(**obs_data),
            reward=payload.get("reward"),
            done=payload.get("done", False),
        )

    def _parse_state(self, payload: dict) -> RehabState:
        return RehabState(**payload)
