---
title: Rehab Scheduler
colorFrom: blue
colorTo: green
sdk: docker
app_port: 8000
pinned: false
---

# Rehabilitation Program Scheduler — OpenEnv Environment

An RL environment where an AI agent acts as a prison rehabilitation program director,
assigning inmates to programs to minimize recidivism risk across the population.

**Team:** NOT_FOUND_101  
**Hackathon:** OpenEnv Challenge — AgentBeats (Meta × Hugging Face)

---

## The Real-World Problem

Over 600,000 people are released from U.S. prisons annually. Within 3 years, 68%
reoffend. The primary driver: inadequate access to rehabilitation programs during
incarceration. Program directors today manage this with spreadsheets and gut feel —
no optimization, no prioritization, no dynamic reallocation when budgets change.

This environment trains AI agents to do what no human case manager has time for:
optimally assign every inmate to the program most likely to reduce their recidivism,
while respecting conflict constraints, refusal preferences, and dynamic budget changes.

---

## Action Space

| Action | Required Fields | Description |
|---|---|---|
| `assign_program` | `inmate_id`, `program_type` | Assign inmate to a program slot |
| `reschedule` | `inmate_id`, `program_type` | Move inmate to a different program |
| `handle_dropout` | `inmate_id`, `replacement_id` | Handle a dropout, optionally fill slot |
| `escalate_case` | `inmate_id` | Flag high-risk inmate for counsellor |
| `reallocate_budget` | `from_program`, `to_program`, `slots` | Move slots between programs |
| `submit_schedule` | — | Terminal action — ends episode, triggers grader |

**Program types:** `education`, `therapy`, `vocational`, `substance_abuse`, `anger_mgmt`

---

## Observation Space

Each `step()` returns:

```json
{
  "done": false,
  "reward": 0.042,
  "inmates": [...],
  "total_inmates": 50,
  "assigned_count": 12,
  "unassigned_count": 38,
  "program_slots": {"therapy": 3, "education": 5, ...},
  "avg_risk_score": 6.2,
  "risk_reduction_so_far": 0.18,
  "constraint_violations": 0,
  "last_action_result": "Assigned I-003 to therapy. Risk reduced by 2.1",
  "steps_remaining": 68
}
```

---

## Tasks

### Task 1 — Basic Allocation (Easy)
- 20 inmates, 25 slots, no conflicts, no refusals
- Agent must assign highest-risk inmates to best-fit programs
- Expected score range: 0.75 – 1.00

### Task 2 — Constrained Scheduling (Medium)
- 50 inmates, 30 slots (60% capacity)
- 5 conflict pairs, 3 program refusals, dynamic high-risk arrivals
- Agent must prioritize correctly and respect all constraints
- Expected score range: 0.50 – 0.85

### Task 3 — Crisis Reoptimization (Hard)
- 200 inmates with dynamic arrivals every 5 steps
- Vocational training budget cut at step 10 — all affected inmates unassigned
- Agent must re-optimize live without restarting the episode
- Expected score range: 0.30 – 0.70

---

## Reward Function

**Step reward:** proportional to risk reduction from each assignment  
`step_reward = risk_reduction / 10.0`

**Final reward (on submit_schedule):**
```
score = 0.60 × (actual_reduction / optimal_reduction)
      + 0.20 × efficiency_score
      + 0.20 × slot_utilization
```

Penalties:
- `-0.15` per constraint violation
- `-0.10` per false escalation (low-risk inmate)
- `-0.05` per wasted slot (dropout without replacement)

---

## Grader

The grader compares the agent's total risk reduction to an oracle greedy optimal
(assigns each inmate their best available program by affinity). Score is always in
`[0.0, 1.0]`.

---

## Setup & Usage

```bash
pip install openenv-core
git clone https://github.com/Mitalimehta02/rehab_scheduler
cd rehab_scheduler
pip install -e .
```

### Run locally
```bash
uvicorn server.app:app --host 0.0.0.0 --port 8000 --reload
```

### Run with Docker
```bash
docker build -t rehab-scheduler -f server/Dockerfile .
docker run -p 8000:8000 rehab-scheduler
```

### Connect as client
```python
from client import RehabEnv
from models import RehabAction, ActionType, ProgramType

with RehabEnv(base_url="http://localhost:8000").sync() as env:
    obs = env.reset(task_id=1, seed=42)
    obs = env.step(RehabAction(
        action_type=ActionType.ASSIGN_PROGRAM,
        inmate_id=obs.observation.waitlist[0],
        program_type=ProgramType.THERAPY,
    ))
    print(obs.observation.avg_risk_score)
```

### Run baseline agent
```bash
export REHAB_ENV_URL=http://localhost:8000
python baseline_agent.py
```

PowerShell:
```powershell
$env:REHAB_ENV_URL="http://localhost:8000"
python baseline_agent.py
```

---

## Baseline Scores

| Task | Difficulty | Baseline (deterministic greedy affinity) |
|---|---|---|
| 1 | Easy | 0.9389 |
| 2 | Medium | 0.9845 |
| 3 | Hard | 0.8464 |

---

## API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | Health check |
| `/tasks` | GET | List all tasks + action schema |
| `/reset` | POST | Start new episode |
| `/step` | POST | Take one action |
| `/state` | GET | Get episode metadata |
| `/grader` | POST | Run grader on completed episode |
| `/baseline` | GET | Run baseline agent on all 3 tasks |
| `/ws` | WebSocket | Persistent session interface |
| `/docs` | GET | Auto-generated API docs |

---

## Project Structure

```
rehab_scheduler/
├── models.py              # Typed Action, Observation, State
├── client.py              # Python client for training code
├── case_generator.py      # Procedural inmate/slot generator
├── baseline_agent.py      # OpenAI API baseline script
├── openenv.yaml           # OpenEnv manifest
├── README.md
└── server/
    ├── app.py             # FastAPI server + all endpoints
    ├── rehab_environment.py  # Environment logic
    ├── requirements.txt
    └── Dockerfile
```

---

## Links

- [Environment Hub](https://huggingface.co/collections/openenv/environment-hub)
- [OpenEnv GitHub](https://github.com/meta-pytorch/OpenEnv)
- [Deployed Space](https://huggingface.co/spaces/AniketAsla/rehab-scheduler)
