# context.md — Project Context for AI Assistants
## Load this file when asking for code help in this project

---

## What This Project Is

An OpenEnv-compatible RL environment for the OpenEnv Hackathon by Meta × Hugging Face.

**Environment name:** Prison Rehabilitation Program Scheduler (`rehab_scheduler`)  
**Team:** NOT_FOUND_101 (Aniket Aslaliya, Mitali Mehta, Aditya Sharma)  
**Deadline:** April 8, 2026, 11:59 PM IST  
**Framework:** OpenEnv (meta-pytorch/OpenEnv on GitHub)  

---

## The Domain

A prison rehabilitation program director must assign inmates to programs
(education, therapy, vocational training, substance abuse treatment, anger
management) to reduce recidivism risk. Resources are limited, constraints exist
(conflict pairs, refusals), and situations change dynamically (budget cuts,
new arrivals).

The AI agent plays the role of this director. It makes sequential decisions
(step() calls) to optimize the population's risk reduction score.

---

## Project File Structure

```
rehab_scheduler/              ← root
├── models.py                 ← ALL typed models live here
├── case_generator.py         ← Procedural inmate/slot generator
├── client.py                 ← Python client for training code
├── baseline_agent.py         ← OpenAI API baseline (hackathon required)
├── openenv.yaml              ← OpenEnv CLI manifest
├── pyproject.toml            ← Package config
├── prd.md                    ← Product requirements
├── skill.md                  ← Engineering patterns
├── context.md                ← This file
├── prompt.md                 ← AI assistant prompts
├── README.md                 ← Hackathon submission README
└── server/
    ├── __init__.py
    ├── app.py                ← FastAPI server + extra endpoints
    ├── rehab_environment.py  ← Core environment logic
    ├── requirements.txt
    └── Dockerfile
```

---

## Key Classes

### RehabAction (models.py)
```python
class RehabAction(Action):
    action_type:    ActionType           # required
    inmate_id:      Optional[str]        # for assign/reschedule/dropout/escalate
    program_type:   Optional[ProgramType] # for assign/reschedule
    replacement_id: Optional[str]        # for handle_dropout
    from_program:   Optional[ProgramType] # for reallocate_budget
    to_program:     Optional[ProgramType] # for reallocate_budget
    slots:          Optional[int]         # for reallocate_budget
```

### RehabObservation (models.py)
Key fields the agent sees each step:
- `inmates`: List of dicts with inmate_id, risk_score, assigned_program, conflict_with, refused_programs
- `program_slots`: Dict of program_type → available slots
- `avg_risk_score`: Current population average risk
- `risk_reduction_so_far`: Progress so far (0.0–1.0)
- `constraint_violations`: Running count of violations
- `last_action_result`: Human-readable feedback on last action
- `steps_remaining`: Steps before forced termination
- `done`: True when episode ends
- `reward`: Step reward (or final score on submit_schedule)

### RehabState (models.py)
- `task_id`: 1, 2, or 3
- `total_inmates`: Current population size
- `initial_avg_risk`: Risk at episode start
- `current_avg_risk`: Risk now
- `total_assignments`: How many inmates assigned
- `total_violations`: Constraint violations triggered
- `grader_score`: Set after SUBMIT_SCHEDULE

### InmateProfile (case_generator.py)
Internal class (NOT Pydantic). Attributes:
- `inmate_id`, `age`, `offence_category`
- `risk_score` (mutable — decreases as programs are assigned)
- `initial_risk` (fixed — used by grader)
- `receptivity` (0.3–1.0, multiplier on program effectiveness)
- `conflict_with`: List of inmate_ids who cannot share sessions
- `refused_programs`: List of ProgramType they won't attend
- `assigned_program`: Current assignment (None if unassigned)
- `is_escalated`: Whether flagged for counsellor

### RehabEnvironment (server/rehab_environment.py)
- Inherits from `openenv.core.env_server.interfaces.Environment`
- `SUPPORTS_CONCURRENT_SESSIONS = True`
- `MAX_STEPS = {1: 40, 2: 80, 3: 200}`
- Internal state: `_inmates`, `_slots`, `_capacity`, `_violations`, `_rng`

---

## Enums (models.py)

### ActionType
```python
assign_program | reschedule | handle_dropout |
escalate_case | reallocate_budget | submit_schedule
```

### ProgramType
```python
education | therapy | vocational | substance_abuse | anger_mgmt
```

### RiskLevel
```python
low (0–3) | medium (4–6) | high (7–10)
```

---

## Task Configurations

| Task | Inmates | Slots | Special |
|---|---|---|---|
| 1 (easy) | 20 | 25 | None |
| 2 (medium) | 50 | 30 | 5 conflict pairs, 3 refusals, 2 dynamic arrivals |
| 3 (hard) | 200 (+20 dynamic) | 140 | Vocational cut at step 10, arrivals every 5 steps |

---

## Grader Formula

```python
final_score = (
    0.60 × (actual_reduction / optimal_reduction)
  + 0.20 × efficiency_score
  + 0.20 × slot_utilization
)

efficiency_score = max(0.0, 1.0 - (violations × 0.05) - (step_ratio × 0.2))
slot_utilization = assigned_count / total_capacity
```

All scores guaranteed in [0.0, 1.0].

---

## Reward Formula (step-level)

```python
# On assign_program or reschedule
step_reward = risk_reduction / 10.0

# On escalate_case (high-risk inmate)
step_reward = 0.03

# On escalate_case (low-risk inmate — penalty)
penalty = 0.1

# On handle_dropout with valid replacement
step_reward = replacement_risk_reduction / 10.0

# On submit_schedule
reward = grader_final_score  # this is the big one
```

---

## Risk Reduction Formula

```python
reduction = PROGRAM_EFFECTIVENESS[program] × inmate.receptivity × affinity_bonus
affinity_bonus = 1.3 if program in OFFENCE_PROGRAM_AFFINITY[offence] else 1.0
risk_score = max(0.0, risk_score - reduction)
```

---

## Program Effectiveness Table

| Program | Effectiveness | Best offence |
|---|---|---|
| education | 1.8 | property, fraud |
| therapy | 2.2 | drug, violent |
| vocational | 1.5 | property, fraud |
| substance_abuse | 2.5 | drug, dui |
| anger_mgmt | 2.0 | violent, dui |

---

## Required Hackathon Endpoints

These MUST exist and respond correctly or submission is disqualified:

```
GET  /health     → {"status": "healthy"}
GET  /tasks      → [{task_id, name, difficulty, max_steps, action_schema}]
POST /grader     → {grader_score: float, steps_taken: int, ...}
GET  /baseline   → {scores: {task_1: {...}, task_2: {...}, task_3: {...}}}
POST /reset      → RehabObservation
POST /step       → RehabObservation
GET  /state      → RehabState
WS   /ws         → WebSocket session
```

---

## OpenEnv Version Compatibility

- `openenv-core >= 0.2.2`
- Imports: `from openenv.core.env_server import Action, Observation, create_fastapi_app`
- Imports: `from openenv.core.env_server.interfaces import Environment`
- Imports: `from openenv.core.env_server.types import State`
- Imports: `from openenv.core.env_client import EnvClient`
- Imports: `from openenv.core.client_types import StepResult`

---

## Environment Variables Used

| Variable | Where | Purpose |
|---|---|---|
| `OPENAI_API_KEY` | baseline_agent.py | OpenAI API access |
| `REHAB_ENV_URL` | baseline_agent.py | Target environment URL |
| `PYTHONPATH` | Dockerfile | Import path for server/ |
| `ENABLE_WEB_INTERFACE` | HF Spaces | Enable /web Gradio UI |

---

## Known Constraints / Rules

1. All models use Pydantic v2 — `model_dump()` not `dict()`
2. `random.Random(seed)` always used — never `import random; random.xxx()`
3. `InmateProfile.risk_score` is mutable (changes during episode)
4. `InmateProfile.initial_risk` is immutable (used by grader)
5. `_check_conflict()` must run before every assignment
6. `_slots[program]` can never go below 0
7. `done=True` is set only by `submit_schedule` or max steps reached
8. Step count increments at the top of every `step()` call
9. Task 3 budget cut (vocational removed) happens exactly at step 10
10. Task 3 dynamic arrivals happen every 5 steps from the dynamic_pool

---

## What NOT to Change Without Team Discussion

- Grader formula weights (0.60 / 0.20 / 0.20)
- Task seeds (42 is the baseline seed)
- MAX_STEPS per task
- Program effectiveness values
- Conflict and refusal generation logic in case_generator.py
- The `optimal_score` calculation (it's the grader denominator)
