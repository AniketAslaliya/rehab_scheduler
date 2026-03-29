"""
Rehabilitation Scheduler — Baseline Inference Script
Uses Gemini (via OpenAI-compatible API) by default to run a baseline agent
against all 3 tasks and produces reproducible scores.

Usage:
    export GEMINI_API_KEY=your-gemini-api-key
    export REHAB_ENV_URL=https://YOUR_USERNAME-rehab-scheduler.hf.space
    python baseline_agent.py

    # Or run against local server:
    export REHAB_ENV_URL=http://localhost:8000
    python baseline_agent.py
"""

import os
import json
import asyncio
from typing import Optional

from openai import OpenAI
import httpx

# ─────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────

# Gemini is preferred. OPENAI_API_KEY remains as backward-compatible fallback.
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
LLM_API_KEY    = GEMINI_API_KEY or OPENAI_API_KEY
LLM_BASE_URL   = os.environ.get(
    "LLM_BASE_URL",
    "https://generativelanguage.googleapis.com/v1beta/openai/",
)
ENV_BASE_URL   = os.environ.get("REHAB_ENV_URL", "https://AniketAsla-rehab-scheduler.hf.space")
MODEL          = os.environ.get("LLM_MODEL", "gemini-2.0-flash")
SEED           = 42

# ─────────────────────────────────────────────
# System prompt for the agent
# ─────────────────────────────────────────────

SYSTEM_PROMPT = """
You are an expert prison rehabilitation program director.
Your goal is to assign rehabilitation programs to inmates to maximize
recidivism reduction (lower risk scores) across the entire population.

PROGRAMS AVAILABLE:
- education:       GED, literacy, academic courses
- therapy:         individual/group counselling
- vocational:      job skills, trade training
- substance_abuse: drug and alcohol rehabilitation
- anger_mgmt:      anger management sessions

STRATEGY:
1. Prioritize high-risk inmates first (highest risk_score)
2. Match program to offence category for affinity bonus:
   - drug → substance_abuse or therapy
   - violent → anger_mgmt or therapy
   - property → vocational or education
   - fraud → education or vocational
   - dui → substance_abuse or anger_mgmt
3. Check conflict_with before assigning — never put conflicting
   inmates in the same program
4. Never assign a program in an inmate's refused_programs list
5. Check program_slots — only assign to programs with slots > 0
6. Use submit_schedule when all possible assignments are made

OUTPUT FORMAT (strict JSON only, no explanation):
{"action_type": "assign_program", "inmate_id": "I-003", "program_type": "therapy"}
{"action_type": "submit_schedule"}
"""


# ─────────────────────────────────────────────
# Simple HTTP client for the environment
# ─────────────────────────────────────────────

class RehabEnvClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.client   = httpx.Client(timeout=30.0)

    def reset(self, task_id: int = 1, seed: int = SEED) -> dict:
        r = self.client.post(
            f"{self.base_url}/reset",
            json={"task_id": task_id, "seed": seed},
        )
        r.raise_for_status()
        return r.json()

    def step(self, action: dict) -> dict:
        r = self.client.post(f"{self.base_url}/step", json=action)
        r.raise_for_status()
        return r.json()

    def state(self) -> dict:
        r = self.client.get(f"{self.base_url}/state")
        r.raise_for_status()
        return r.json()

    def close(self):
        self.client.close()


# ─────────────────────────────────────────────
# Agent loop
# ─────────────────────────────────────────────

def build_user_message(obs: dict) -> str:
    """Convert observation dict to a clear agent prompt."""
    unassigned = [
        i for i in obs.get("inmates", [])
        if i["assigned_program"] is None
    ]
    # Only show top 10 by risk to keep context short
    top_unassigned = sorted(unassigned, key=lambda x: -x["risk_score"])[:10]

    return f"""
CURRENT STATE:
- Total inmates: {obs.get("total_inmates")}
- Assigned: {obs.get("assigned_count")} | Unassigned: {obs.get("unassigned_count")}
- Avg risk score: {obs.get("avg_risk_score")} | Reduction so far: {obs.get("risk_reduction_so_far", 0):.1%}
- Steps remaining: {obs.get("steps_remaining")}
- Violations so far: {obs.get("constraint_violations")}

PROGRAM SLOTS AVAILABLE:
{json.dumps(obs.get("program_slots", {}), indent=2)}

TOP UNASSIGNED INMATES (by risk):
{json.dumps(top_unassigned, indent=2)}

LAST ACTION RESULT: {obs.get("last_action_result")}

Choose your next action as strict JSON.
If no more useful assignments exist, submit: {{"action_type": "submit_schedule"}}
"""


def run_task(task_id: int, verbose: bool = True) -> dict:
    """Run one full episode for a given task. Returns result dict."""
    if not LLM_API_KEY:
        raise ValueError("Set GEMINI_API_KEY (or OPENAI_API_KEY as fallback).")

    oai = OpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)
    env = RehabEnvClient(ENV_BASE_URL)

    print(f"\n{'='*60}")
    print(f"Task {task_id} — starting episode (seed={SEED})")
    print(f"{'='*60}")

    obs = env.reset(task_id=task_id, seed=SEED)
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    step = 0
    final_reward = 0.0

    while not obs.get("done", False):
        step += 1
        user_msg = build_user_message(obs)
        messages.append({"role": "user", "content": user_msg})

        # Call LLM through OpenAI-compatible API (Gemini by default).
        response = oai.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=0.0,
            seed=SEED,
            max_tokens=200,
        )

        action_str = response.choices[0].message.content.strip()
        messages.append({"role": "assistant", "content": action_str})

        try:
            action = json.loads(action_str)
        except json.JSONDecodeError:
            print(f"Step {step}: Invalid JSON from model — submitting.")
            action = {"action_type": "submit_schedule"}

        if verbose:
            print(f"Step {step:3d}: {action}")

        obs = env.step(action)

        if obs.get("reward") is not None:
            final_reward = obs["reward"]

        # Safety: force submit if steps exhausted
        if obs.get("steps_remaining", 1) <= 0 and not obs.get("done"):
            obs = env.step({"action_type": "submit_schedule"})
            final_reward = obs.get("reward", final_reward)
            break

    state = env.state()
    env.close()

    result = {
        "task_id":          task_id,
        "seed":             SEED,
        "model":            MODEL,
        "steps_taken":      step,
        "final_score":      final_reward,
        "total_assignments": state.get("total_assignments"),
        "total_violations": state.get("total_violations"),
        "current_avg_risk": state.get("current_avg_risk"),
        "initial_avg_risk": state.get("initial_avg_risk"),
    }

    print(f"\nTask {task_id} complete:")
    print(f"  Score:       {final_reward:.4f}")
    print(f"  Assignments: {state.get('total_assignments')}")
    print(f"  Violations:  {state.get('total_violations')}")
    print(f"  Risk:        {state.get('initial_avg_risk'):.2f} → {state.get('current_avg_risk'):.2f}")

    return result


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────

def main():
    print("Rehabilitation Scheduler — Baseline Agent")
    print(f"Environment: {ENV_BASE_URL}")
    print(f"Model:       {MODEL}")

    all_results = {}
    for task_id in [1, 2, 3]:
        try:
            result = run_task(task_id)
            all_results[f"task_{task_id}"] = result
        except Exception as e:
            print(f"Task {task_id} failed: {e}")
            all_results[f"task_{task_id}"] = {"error": str(e)}

    print(f"\n{'='*60}")
    print("BASELINE RESULTS SUMMARY")
    print(f"{'='*60}")
    for task, result in all_results.items():
        score = result.get("final_score", "error")
        print(f"  {task}: {score}")

    # Save to file for submission
    with open("baseline_results.json", "w") as f:
        json.dump(all_results, f, indent=2)
    print("\nResults saved to baseline_results.json")


if __name__ == "__main__":
    main()
