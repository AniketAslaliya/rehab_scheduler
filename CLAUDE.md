# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Reinforcement Learning environment for a prison rehabilitation program scheduler, built for the OpenEnv Challenge (Meta × Hugging Face AgentBeats hackathon). The environment simulates assigning inmates to rehab programs to minimize recidivism risk.

## Setup & Commands

```bash
# Install dependencies
pip install openenv-core>=0.2.2
pip install -e .

# Run server (development)
uvicorn server.app:app --host 0.0.0.0 --port 8000 --reload

# Run server (production via Docker)
docker build -t rehab-scheduler -f server/Dockerfile .
docker run -p 8000:8000 rehab-scheduler

# Run baseline agent (requires OpenAI key)
export OPENAI_API_KEY=sk-...
export REHAB_ENV_URL=http://localhost:8000
python baseline_agent.py

# Validate syntax
python -m py_compile <file>.py

# OpenEnv validation
openenv validate --verbose
```

No formal test suite — validation is done via the OpenEnv framework and `docker build && docker run`.

## Architecture

**Client-server RL pattern:**

- `models.py` — Pydantic models: `InmateProfile`, `RehabAction`, `RehabObservation`, `RehabState`, and enums (`ActionType`, `ProgramType`, `RiskLevel`)
- `case_generator.py` — Procedurally generates 3 task difficulties (20/50/200 inmates) with seeded RNG for reproducibility. Contains `compute_risk_reduction()` and `compute_optimal_score()` for grading baseline.
- `server/rehab_environment.py` — Core `RehabEnvironment` class implementing OpenEnv's `reset(task_id, seed)` / `step(action)` / `state` interface. Contains the grader `_grade()` function.
- `server/app.py` — FastAPI server exposing OpenEnv standard endpoints (`/reset`, `/step`, `/state`, `/ws`) plus hackathon-required endpoints (`/tasks`, `/grader`, `/baseline`).
- `baseline_agent.py` — GPT-4o agent using OpenAI API. Prioritizes high-risk inmates, matches program to offence category for affinity bonus. Saves results to `baseline_results.json`.
- `client.py` — Typed Python client (`RehabEnv`) for training/research use; supports sync and async.

## Key Domain Logic

**Grader formula:**
```
score = 0.60 × (actual_reduction / optimal)
      + 0.20 × efficiency_score
      + 0.20 × slot_utilization
Penalties: -0.15/constraint violation, -0.10/false escalation, -0.05/wasted slot
```

**Program effectiveness multipliers:** Substance Abuse (2.5) > Therapy (2.2) > Anger Mgmt (2.0) > Education (1.8) > Vocational (1.5)

**Actions:** `assign_program`, `reschedule`, `handle_dropout`, `escalate_case`, `reallocate_budget`, `submit_schedule` (terminal — triggers grader)

**Task difficulties:**
- Task 1 (easy): 20 inmates, 25 slots, no constraints, max 40 steps
- Task 2 (medium): 50 inmates, 30 slots, 5 conflict pairs, 3 refusals, max 80 steps
- Task 3 (hard): 200 inmates, dynamic arrivals every 5 steps, budget cut at step 10, max 200 steps

## Deployment

Target: Hugging Face Spaces. The `openenv.yaml` manifest declares environment class, 3 tasks, and endpoint mappings. `server/Dockerfile` uses `python:3.11-slim`, exposes port 8000, runs 2 uvicorn workers.
