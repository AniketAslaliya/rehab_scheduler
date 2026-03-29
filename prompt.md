# prompt.md — AI Assistant Prompts for This Project
## Copy-paste these into VS Code Copilot Chat, Claude, or any AI assistant

---

## HOW TO USE THIS FILE

Before using any prompt below:
1. Open `context.md` and paste its full contents first
2. Then paste the specific prompt you need
3. The AI will have full project context and produce correct code

---

## MASTER CONTEXT PRIMER
**Paste this FIRST before any other prompt in a new conversation:**

```
I am building an OpenEnv RL environment called "Prison Rehabilitation Program 
Scheduler" for the OpenEnv Hackathon by Meta × Hugging Face.

Here is the full project context:
[PASTE ENTIRE context.md HERE]

Here is the engineering skill reference:
[PASTE ENTIRE skill.md HERE]

Now I am ready for specific tasks. Wait for my next message.
```

---

## SECTION 1 — DEBUGGING PROMPTS

### 1.1 — Fix an Import Error
```
I'm getting this import error in my OpenEnv environment:
[PASTE ERROR HERE]

The file structure is:
rehab_scheduler/
├── models.py
├── case_generator.py
└── server/
    ├── app.py
    └── rehab_environment.py

The server files need to import from models.py and case_generator.py
which are one directory above. Fix the import without changing the file structure.
```

### 1.2 — Fix a Pydantic Validation Error
```
I'm getting a Pydantic validation error when calling POST /step:
[PASTE ERROR AND REQUEST BODY HERE]

My RehabAction model is defined as:
[PASTE models.py ACTION CLASS HERE]

Fix the request body or model definition to make validation pass.
This project uses Pydantic v2. Use model_dump() not dict().
```

### 1.3 — Fix a Docker Build Error
```
My Docker build is failing with:
[PASTE DOCKER ERROR HERE]

My Dockerfile is:
[PASTE Dockerfile HERE]

My project structure is:
rehab_scheduler/
├── models.py
├── case_generator.py
└── server/
    ├── app.py
    ├── rehab_environment.py
    ├── requirements.txt
    └── Dockerfile

The server files import from models.py (one level up).
Fix the Dockerfile so imports work correctly inside the container.
```

### 1.4 — Grader Returns Same Score for Every Seed
```
My grader is returning the same score regardless of the seed I pass.
This means my case generation isn't using the seed correctly.

Current case_generator.py:
[PASTE RELEVANT SECTION]

The grader formula is:
final_score = 0.60 × reduction_score + 0.20 × efficiency + 0.20 × utilization

Fix the seed propagation so that different seeds produce different inmate
populations and therefore different grader scores. 
Use random.Random(seed) not global random state.
```

### 1.5 — openenv validate Fails
```
Running openenv validate --verbose gives:
[PASTE VALIDATION ERROR]

My openenv.yaml is:
[PASTE openenv.yaml]

My app.py endpoints are:
[PASTE endpoint list]

Fix whatever is causing validation to fail. The required endpoints are:
/health, /tasks, /grader, /baseline, /reset, /step, /state, /ws
```

---

## SECTION 2 — FEATURE ADDITION PROMPTS

### 2.1 — Add a New Action Type
```
I need to add a new action type called "REQUEST_COUNSELLOR" to my 
Rehabilitation Scheduler environment.

This action:
- Takes inmate_id as input
- Requests a one-on-one counsellor session (scarce resource: max 5 per episode)
- If counsellor available: reduces inmate risk_score by 1.5, marks is_counselled=True
- If no counsellors left: returns error message with -0.05 penalty
- Reward: 0.15 if high-risk inmate (risk >= 7), -0.05 if low-risk (waste of resource)

Current ActionType enum values:
assign_program | reschedule | handle_dropout | escalate_case | 
reallocate_budget | submit_schedule

Add this action type to:
1. models.py (ActionType enum + RehabAction fields)
2. server/rehab_environment.py (handler method + dispatch dict)
3. RehabObservation (add counsellors_remaining field)
4. server/app.py /tasks endpoint (update action_schema)

Use the same handler pattern as _handle_escalate().
```

### 2.2 — Add a New Task Difficulty
```
I want to add Task 4 (extreme difficulty) to my environment.

Task 4 specs:
- 500 inmates
- Only 40% slot capacity (200 slots across 5 programs)
- 20% of inmates have conflict clusters (groups of 4 who all conflict)
- 40% refusal rate
- Dynamic arrivals every 3 steps (10 inmates each time)
- TWO budget cuts: vocational at step 10, education at step 25
- Max 400 steps

Add Task 4 to:
1. case_generator.py — new generate_task_4() function
2. server/rehab_environment.py — update MAX_STEPS dict and reset() validation
3. server/app.py — add task 4 to /tasks endpoint response

Follow the exact same pattern as generate_task_3().
Use seed=42 default. Make sure compute_optimal_score() works with task 4.
```

### 2.3 — Improve the Baseline Agent
```
My current baseline agent in baseline_agent.py uses a simple greedy strategy:
assign highest-risk inmate to first available slot each step.

Improve it to use a smarter strategy:
1. Sort unassigned inmates by risk_score descending
2. For each inmate, find their BEST program (highest expected reduction)
   based on offence_category → program affinity mapping:
   drug → substance_abuse or therapy
   violent → anger_mgmt or therapy
   property → vocational or education
   fraud → education or vocational
   dui → substance_abuse or anger_mgmt
3. Check conflict_with before assigning
4. Check refused_programs before assigning
5. Check program_slots > 0 before assigning
6. If no valid assignment exists for an inmate, skip them (don't waste a step)
7. Submit when all assignable inmates are assigned

The agent still uses the OpenAI API with the same build_user_message() function.
Update the SYSTEM_PROMPT to reflect the smarter strategy.
Keep all the same environment variable names (OPENAI_API_KEY, REHAB_ENV_URL).
```

### 2.4 — Add Partial Observability (Advanced)
```
Currently my environment exposes ALL inmate risk scores to the agent.
I want to add a partial observability mode where:
- Only inmates in the top 50% by risk are fully visible
- The bottom 50% show "risk_score": null (agent must investigate)
- Add new action: "ASSESS_INMATE" (inmate_id) — reveals true risk score
  - Costs one step, no direct reward
  - But enables better assignment decisions

Modify:
1. models.py — add ASSESS_INMATE to ActionType, add is_assessed field to inmate dict
2. server/rehab_environment.py:
   - In _make_observation(): mask risk_score to null if not assessed and low-risk
   - Add _handle_assess() method
   - Add to dispatch dict
3. RehabObservation: add assessed_count field

Make partial observability optional — add partial_obs: bool = False parameter
to reset() so existing tests still pass.
```

---

## SECTION 3 — TESTING PROMPTS

### 3.1 — Write Unit Tests for the Grader
```
Write pytest unit tests for the grader in server/rehab_environment.py.

The grader function signature is:
def _grade(inmates, violations, wasted_slots, total_slots, 
           steps_taken, max_steps, optimal_score) -> float

Tests must verify:
1. Score is always in [0.0, 1.0] for any valid input
2. Perfect assignment (all high-risk inmates, no violations) scores >= 0.85
3. Zero assignments scores near 0.0
4. Each violation reduces score by ~0.05
5. Different seeds produce different scores
6. Score with violations < score without violations (same assignments)

Use the actual InmateProfile class from case_generator.py.
Import patterns must work from the project root.
File: tests/test_grader.py
```

### 3.2 — Write Integration Tests for All Endpoints
```
Write pytest integration tests that start the FastAPI server and test
all required hackathon endpoints.

Test all of these:
GET  /health     → status 200, body contains "healthy"
GET  /tasks      → status 200, body contains 3 tasks, each with action_schema
POST /reset      → status 200, body has all RehabObservation fields
POST /step       → status 200, body has done, reward, last_action_result
GET  /state      → status 200, body has task_id, step_count
POST /grader     → status 200, body has grader_score in [0.0, 1.0]
GET  /baseline   → status 200, body has scores for task_1, task_2, task_3

Use httpx.TestClient(app) — no need to start a real server.
Use from server.app import app to get the FastAPI instance.
File: tests/test_endpoints.py
```

### 3.3 — Test Reproducibility
```
Write a test that proves our environment is reproducible:
- Run 3 complete episodes with task_id=1, seed=42
- Submit schedule at the end of each
- Assert all 3 final scores are identical (== not just close)
- Run same test with seed=99 and assert those 3 are also identical
- Assert seed=42 score != seed=99 score (different seeds → different results)

Use the RehabEnvironment class directly (not via HTTP).
File: tests/test_reproducibility.py
```

---

## SECTION 4 — DEPLOYMENT PROMPTS

### 4.1 — Fix HF Spaces Deployment
```
My openenv push is failing with:
[PASTE ERROR]

My openenv.yaml is:
[PASTE openenv.yaml]

My Dockerfile is:
[PASTE Dockerfile]

Fix the deployment configuration. The Space URL should be:
https://YOUR_USERNAME-rehab-scheduler.hf.space

Common issues to check:
- Dockerfile COPY paths relative to build context
- requirements.txt location
- PYTHONPATH environment variable
- Port must be 8000 (HF Spaces default)
- CMD must use uvicorn
```

### 4.2 — Generate GitHub Actions CI
```
Write a GitHub Actions workflow file (.github/workflows/validate.yml) that:
1. Runs on every push to main and every pull request
2. Sets up Python 3.11
3. Installs dependencies from server/requirements.txt
4. Runs: python -m py_compile on all .py files
5. Starts the uvicorn server in the background
6. Waits 5 seconds for startup
7. Hits /health endpoint and fails if not 200
8. Hits /tasks endpoint and fails if not 200
9. Runs openenv validate --verbose
10. Fails the workflow if any step fails

The workflow should NOT run the baseline agent (requires API key).
```

---

## SECTION 5 — EXPLANATION PROMPTS

### 5.1 — Explain the Reward Function to a Judge
```
I need to write a clear explanation of my reward function for the hackathon
README. The audience is Meta and Hugging Face engineers judging the submission.

The reward function is:
[PASTE _grade() function from rehab_environment.py]

Write 3–4 sentences explaining:
1. What each component measures (reduction, efficiency, utilization)
2. Why the 60/20/20 weights were chosen
3. How the oracle optimal normalization works
4. Why this produces a rich gradient signal for RL training (not just binary reward)

Tone: technical but accessible. No bullet points — prose only.
```

### 5.2 — Explain an Action Handler to a Teammate
```
Explain what this action handler does and why it's implemented this way:
[PASTE _handle_reschedule() or any handler]

The explanation should cover:
1. What the action does in real-world terms
2. The validation checks and why each exists
3. How the state changes after the action
4. What reward/penalty is applied and why
5. What could go wrong and how it's handled

Target audience: Mitali or Aditya who needs to test this function.
```

---

## SECTION 6 — README / DOCUMENTATION PROMPTS

### 6.1 — Write the Environment Description Section
```
Write the "Environment Description" section of the README for my
Prison Rehabilitation Program Scheduler OpenEnv environment.

Key facts to include:
- Domain: prison rehabilitation resource allocation
- Agent role: program director making assignment decisions
- Why it matters: 68% recidivism rate, 600K released annually
- What makes it a good RL environment: multi-turn, dynamic state,
  partial rewards every step, cascading consequences
- 3 tasks of increasing difficulty

Tone: professional but compelling. This is the first thing judges read.
Length: 150–200 words. No bullet points — prose paragraphs.
Do NOT use the words "straightforward", "innovative", or "leveraging".
```

### 6.2 — Write Baseline Score Commentary
```
I've run my baseline agent (greedy GPT-4o) on all 3 tasks and got:
Task 1: 0.82
Task 2: 0.61
Task 3: 0.44

Write 3 sentences for the README that:
1. States these scores clearly
2. Explains WHY scores decrease across tasks (more constraints, dynamic changes)
3. Notes what a trained RL agent should be able to achieve with these
   as a lower bound

Tone: factual and specific. Judges use this to calibrate the environment difficulty.
```

---

## QUICK REFERENCE — COMMON CODE PATTERNS

### Correct action dispatch pattern
```python
handler = {
    ActionType.ASSIGN_PROGRAM: self._handle_assign,
    ActionType.SUBMIT_SCHEDULE: self._handle_submit,
}.get(action.action_type)

if handler is None:
    return "Unknown action", False, -0.1, 0.0, False

result, valid, penalty, reward, done = handler(action)
```

### Correct observation construction
```python
return RehabObservation(
    done=done,
    reward=reward,
    # ... all other fields
)
```

### Correct Pydantic enum serialization
```python
# In to_dict() on InmateProfile
"assigned_program": self.assigned_program.value if self.assigned_program else None
"refused_programs": [p.value for p in self.refused_programs]
```

### Correct seeded generation
```python
def generate_task_1(seed: int = 42):
    rng = random.Random(seed)
    return [_make_inmate(i, rng) for i in range(20)]
```

### Correct test client usage
```python
from fastapi.testclient import TestClient
from server.app import app

client = TestClient(app)
response = client.post("/reset", json={"task_id": 1, "seed": 42})
assert response.status_code == 200
```
