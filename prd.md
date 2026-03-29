# PRD — Prison Rehabilitation Program Scheduler
## OpenEnv Hackathon Submission | Team NOT_FOUND_101

---

## 1. Product Overview

### 1.1 What We Are Building
An OpenEnv-compatible RL environment that simulates a prison rehabilitation
program director's decision-making workflow. An AI agent receives a population
of inmates with varying risk profiles, a limited pool of program slots, and
operational constraints — and must optimally assign inmates to programs to
minimize recidivism across the population.

### 1.2 Why It Exists
- 600,000 people are released from US prisons annually
- 68% reoffend within 3 years
- Primary cause: inadequate, poorly allocated rehabilitation programs
- Current allocation method: spreadsheets + gut feel by overworked case managers
- No existing RL environment models this problem
- Judges can immediately understand the stakes without domain expertise

### 1.3 What Success Looks Like
- `openenv validate` passes with zero errors
- `docker build && docker run` works cleanly
- All 3 endpoints (/tasks, /grader, /baseline) respond correctly
- Baseline agent produces reproducible scores across 3 runs
- Judges score >= 80/100 overall

---

## 2. Stakeholders

| Role | Person | Responsibility |
|---|---|---|
| Team Lead | Aniket Aslaliya | Architecture, environment logic, final submission |
| Member | Mitali Mehta | Baseline agent, README, testing |
| Member | Aditya Sharma | Docker, HF Spaces deployment, CI validation |

---

## 3. Functional Requirements

### 3.1 Core Interface (Must Have)
- [ ] `reset(task_id, seed)` — starts a new episode, returns initial observation
- [ ] `step(action)` — processes one agent action, returns updated observation
- [ ] `state` property — returns episode-level metadata
- [ ] All return types are typed Pydantic models
- [ ] WebSocket endpoint `/ws` for persistent sessions

### 3.2 Action Space (Must Have)
All 6 action types must be implemented and validated:
- [ ] `assign_program` — inmate_id + program_type
- [ ] `reschedule` — inmate_id + program_type
- [ ] `handle_dropout` — inmate_id + optional replacement_id
- [ ] `escalate_case` — inmate_id
- [ ] `reallocate_budget` — from_program + to_program + slots
- [ ] `submit_schedule` — terminal action, triggers grader

### 3.3 Tasks (Must Have)
- [ ] Task 1 (easy): 20 inmates, 25 slots, no constraints
- [ ] Task 2 (medium): 50 inmates, 60% capacity, conflicts + refusals
- [ ] Task 3 (hard): 200 inmates, dynamic arrivals, mid-episode budget cut
- [ ] Each task has seeded, reproducible case generation
- [ ] Each task has a deterministic grader returning float in [0.0, 1.0]

### 3.4 Reward Function (Must Have)
- [ ] Step reward: proportional to risk reduction per assignment
- [ ] Final reward: weighted formula (60% reduction + 20% efficiency + 20% utilization)
- [ ] Penalties: constraint violations, false escalations, wasted slots
- [ ] Reward is always in [0.0, 1.0]
- [ ] Partial rewards every step (not just at episode end)

### 3.5 Hackathon-Required Endpoints (Must Have)
- [ ] `GET /health` — returns {"status": "healthy"}
- [ ] `GET /tasks` — returns all task configs + action schema
- [ ] `POST /grader` — runs grader on completed episode
- [ ] `GET /baseline` — runs baseline on all 3 tasks, returns scores
- [ ] `POST /reset` — HTTP reset endpoint
- [ ] `POST /step` — HTTP step endpoint
- [ ] `GET /state` — HTTP state endpoint

### 3.6 Deployment (Must Have)
- [ ] Working Dockerfile (docker build + docker run)
- [ ] Deployed HF Space (openenv push)
- [ ] openenv.yaml manifest
- [ ] openenv validate passes

### 3.7 Baseline Script (Must Have)
- [ ] Uses OpenAI API client (not LangChain, not anything else)
- [ ] Reads OPENAI_API_KEY from environment variable
- [ ] Reads REHAB_ENV_URL from environment variable
- [ ] Produces reproducible scores on all 3 tasks
- [ ] Saves results to baseline_results.json

### 3.8 Documentation (Must Have)
- [ ] README.md with: problem description, action space, observation space,
      task descriptions, setup instructions, baseline scores, API endpoints
- [ ] Inline code comments on all non-obvious logic
- [ ] Type hints on every function signature

---

## 4. Non-Functional Requirements

### 4.1 Performance
- Single episode (Task 1) must complete in < 5 seconds on CPU
- Server must handle 10 concurrent WebSocket sessions minimum
- All endpoint responses < 500ms on HF Spaces free tier

### 4.2 Reproducibility
- Identical seed → identical case generation → identical optimal score
- Baseline script run 3 times → identical scores each time
- `random.Random(seed)` used throughout (not global random state)

### 4.3 Code Quality
- Python 3.11
- Pydantic v2 models (model_dump not dict())
- Type hints everywhere
- No circular imports
- All files pass `python -m py_compile`

### 4.4 Compatibility
- openenv-core >= 0.2.2
- FastAPI >= 0.104.0
- Pydantic >= 2.0.0
- Python >= 3.10

---

## 5. Out of Scope

- Real inmate data (all data is procedurally generated)
- Multi-agent training (single agent only)
- Web UI beyond the OpenEnv default /web endpoint
- Authentication or rate limiting
- Persistent storage between episodes
- Any external API calls from environment logic

---

## 6. Grader Specification

### 6.1 Formula
```
final_score = (
    0.60 × (actual_risk_reduction / optimal_risk_reduction)
  + 0.20 × efficiency_score
  + 0.20 × slot_utilization
)

efficiency_score = max(0, 1.0 - (violations × 0.05) - (step_ratio × 0.2))
slot_utilization = assigned_count / total_capacity
```

### 6.2 Oracle Optimal
- Greedy oracle assigns each inmate their highest-reduction program
- Respects slot capacity
- Sorted by risk score descending (highest risk served first)
- Used as denominator to normalize agent score to [0, 1]

### 6.3 Grader Contract
- Always returns float in [0.0, 1.0]
- Deterministic given same seed
- Called on SUBMIT_SCHEDULE action
- Also callable via POST /grader endpoint

---

## 7. Case Generator Specification

### 7.1 Inmate Attributes
| Attribute | Type | Range | Description |
|---|---|---|---|
| inmate_id | str | I-001..I-NNN | Unique identifier |
| age | int | 18–55 | Inmate age |
| offence_category | str | drug/violent/property/fraud/dui | Crime type |
| risk_score | float | 0.0–10.0 | Recidivism risk (higher = worse) |
| receptivity | float | 0.3–1.0 | Program responsiveness |
| conflict_with | List[str] | inmate_ids | Cannot share any session |
| refused_programs | List[ProgramType] | 0–2 programs | Will not attend |

### 7.2 Program Effectiveness
| Program | Base Effectiveness | Best For |
|---|---|---|
| education | 1.8 | property, fraud |
| therapy | 2.2 | drug, violent |
| vocational | 1.5 | property, fraud |
| substance_abuse | 2.5 | drug, dui |
| anger_mgmt | 2.0 | violent, dui |

Risk reduction formula:
```
reduction = effectiveness × receptivity × affinity_bonus
affinity_bonus = 1.3 if program matches offence category else 1.0
```

---

## 8. Deadlines

| Milestone | Date | Owner |
|---|---|---|
| Round 1 opens, problem statement chosen | April 1, 2026 | All |
| openenv init scaffold run | April 1, 2026 EOD | Aniket |
| models.py + case_generator.py complete | April 2, 2026 | Aniket |
| rehab_environment.py complete + local test | April 3, 2026 | Aniket |
| server/app.py + all endpoints working | April 4, 2026 | Mitali |
| baseline_agent.py + reproducible scores | April 5, 2026 | Mitali |
| Docker build + HF Spaces deploy | April 6, 2026 | Aditya |
| openenv validate passes | April 6, 2026 | Aditya |
| README polished + baseline scores recorded | April 7, 2026 | Mitali |
| Final submission | April 8, 2026 11:59 PM IST | Aniket |

---

## 9. Risk Register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| openenv-core API changes | Medium | High | Pin to 0.2.2, test on exact version |
| HF Spaces deployment fails | Low | High | Test docker run locally first |
| Baseline scores not reproducible | Medium | High | Use seeded Random, fix model temperature=0 |
| Grader always returns same score | Low | Critical | Unit test with multiple seeds |
| Import errors in Docker | Medium | High | Test docker build before deadline day |
| openenv validate fails | Medium | High | Run locally daily from April 1 |

---

## 10. Acceptance Criteria (Pre-Submission Checklist)

Before submitting the HF Spaces URL, every item must be ✅:

- [ ] `curl https://YOUR_SPACE.hf.space/health` returns 200
- [ ] `curl https://YOUR_SPACE.hf.space/tasks` returns 3 tasks with action schema
- [ ] `POST /reset {"task_id": 1, "seed": 42}` returns valid observation
- [ ] `POST /step {"action_type": "submit_schedule"}` returns reward in [0, 1]
- [ ] `GET /baseline` returns scores for all 3 tasks
- [ ] `python baseline_agent.py` runs without errors 3 times, same scores each time
- [ ] `docker build -t rehab -f server/Dockerfile . && docker run -p 8000:8000 rehab` works
- [ ] `openenv validate --verbose` passes with zero errors
- [ ] README.md contains all required sections
- [ ] baseline_results.json exists and has scores for all 3 tasks
