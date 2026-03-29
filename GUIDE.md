# Complete Beginner Guide — Rehab Scheduler
## From Zero to Hackathon Submission, Step by Step
### Team NOT_FOUND_101

---

## Before You Read Anything Else

This guide assumes you have never built an OpenEnv environment before.
Every command is written out in full. Every file location is specified exactly.
Every PR is described with what goes in it and what the reviewer should check.

Read the entire guide once before doing anything. Then come back and follow it step by step.

**Golden rule: never skip a verification step. If a curl command doesn't return
what this guide says it should, stop and fix it before moving forward.**

---

## Your Complete Project File Map

```
rehab_scheduler/                  ← your GitHub repo root
│
├── .github/
│   └── workflows/
│       └── validate.yml          ← CI pipeline (created in Phase 2)
│
├── .vscode/
│   └── settings.json             ← VS Code settings (created in Phase 1)
│
├── tests/
│   ├── __init__.py
│   ├── test_grader.py            ← unit tests (Phase 4)
│   ├── test_endpoints.py         ← integration tests (Phase 4)
│   └── test_reproducibility.py   ← reproducibility tests (Phase 4)
│
├── models.py                     ← ALREADY WRITTEN — do not recreate
├── case_generator.py             ← ALREADY WRITTEN — do not recreate
├── client.py                     ← ALREADY WRITTEN — do not recreate
├── baseline_agent.py             ← ALREADY WRITTEN — do not recreate
├── openenv.yaml                  ← ALREADY WRITTEN — update username
├── pyproject.toml                ← ALREADY WRITTEN — do not recreate
│
├── prd.md                        ← ALREADY WRITTEN — your checklist
├── skill.md                      ← ALREADY WRITTEN — your reference
├── context.md                    ← ALREADY WRITTEN — for AI assistants
├── prompt.md                     ← ALREADY WRITTEN — copy-paste prompts
├── README.md                     ← ALREADY WRITTEN — update username
│
├── server/
│   ├── __init__.py               ← ALREADY WRITTEN
│   ├── app.py                    ← ALREADY WRITTEN — do not recreate
│   ├── rehab_environment.py      ← ALREADY WRITTEN — do not recreate
│   ├── requirements.txt          ← ALREADY WRITTEN
│   └── Dockerfile                ← ALREADY WRITTEN
│
└── GUIDE.md                      ← THIS FILE
```

**Files marked "ALREADY WRITTEN" were generated for you.
Your job is to copy them into your repo, not rewrite them.**

---

## Phase Overview

| Phase | What You Do | Days | PR # |
|---|---|---|---|
| 0 | Setup your machine | Before April 1 | — |
| 1 | Copy files into repo, verify structure | April 1 | PR-1 |
| 2 | Run locally, fix import errors | April 1–2 | PR-2 |
| 3 | Test all endpoints manually | April 2–3 | PR-3 |
| 4 | Write and run tests | April 3–4 | PR-4 |
| 5 | Docker build and run | April 4–5 | PR-5 |
| 6 | Deploy to HF Spaces | April 5–6 | PR-6 |
| 7 | Run baseline agent, record scores | April 6–7 | PR-7 |
| 8 | Final validation and submit | April 7–8 | PR-8 |

---

---

# PHASE 0 — Machine Setup
## Do This Before April 1st

---

### Step 0.1 — Install Python 3.11

**Check if you already have it:**
```bash
python --version
# Should show: Python 3.11.x
```

**If not, download from:** https://www.python.org/downloads/release/python-3119/
- Windows: download the installer, check "Add Python to PATH"
- Mac: `brew install python@3.11`
- Linux: `sudo apt install python3.11 python3.11-pip`

**Verify:**
```bash
python3.11 --version
# Python 3.11.9
```

---

### Step 0.2 — Install Git

**Check:**
```bash
git --version
# git version 2.x.x
```

**If not installed:** https://git-scm.com/downloads

**Configure your identity (required for commits):**
```bash
git config --global user.name "Aniket Aslaliya"
git config --global user.email "aniketaslaliya@gmail.com"
```

---

### Step 0.3 — Install VS Code

Download from: https://code.visualstudio.com/

**Install these extensions inside VS Code:**
1. Press `Ctrl+Shift+X` (Windows) or `Cmd+Shift+X` (Mac)
2. Search and install each:
   - `Python` (by Microsoft)
   - `Pylance` (by Microsoft)
   - `GitHub Copilot` (if you have access)
   - `GitLens` (for PR workflow visibility)
   - `YAML` (by Red Hat — for openenv.yaml)
   - `REST Client` (for testing endpoints without curl)

---

### Step 0.4 — Install Docker

**Download from:** https://www.docker.com/products/docker-desktop/

**After install, verify:**
```bash
docker --version
# Docker version 24.x.x
docker run hello-world
# Should print "Hello from Docker!"
```

---

### Step 0.5 — Install Hugging Face CLI

```bash
pip install huggingface-hub
huggingface-cli --version
# huggingface-hub/0.x.x
```

**Login to Hugging Face:**
1. Go to https://huggingface.co/settings/tokens
2. Create a new token with "Write" permission
3. Copy the token (starts with `hf_...`)
4. Run:
```bash
huggingface-cli login
# Paste your token when prompted
```

---

### Step 0.6 — Install OpenEnv

```bash
pip install openenv-core
openenv --version
# openenv x.x.x
```

---

### Step 0.7 — Clone Your Repo

```bash
# Replace with your actual GitHub repo URL
git clone https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
cd YOUR_REPO_NAME

# Open in VS Code
code .
```

---

### Step 0.8 — Create VS Code Settings

Inside VS Code, create `.vscode/settings.json`:

```json
{
  "python.defaultInterpreterPath": "python3.11",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": false,
  "python.linting.flake8Enabled": false,
  "editor.formatOnSave": false,
  "files.exclude": {
    "**/__pycache__": true,
    "**/*.pyc": true,
    "**/.pytest_cache": true
  },
  "[python]": {
    "editor.tabSize": 4,
    "editor.insertSpaces": true
  }
}
```

**Commit this:**
```bash
git add .vscode/settings.json
git commit -m "chore: add VS Code settings"
git push origin main
```

---

### Phase 0 Complete Checklist
- [ ] `python3.11 --version` works
- [ ] `git --version` works
- [ ] `docker --version` works
- [ ] `docker run hello-world` works
- [ ] `huggingface-cli login` completed
- [ ] `openenv --version` works
- [ ] VS Code extensions installed
- [ ] Repo cloned and open in VS Code

---

---

# PHASE 1 — Copy Files Into Your Repo
## April 1st — First Thing

---

### Step 1.1 — Create the Folder Structure

Open VS Code terminal (`Ctrl+`` ` on Windows, `Cmd+`` ` on Mac):

```bash
# Make sure you are in your repo root
pwd
# Should show: /path/to/YOUR_REPO_NAME

# Create all required directories
mkdir -p server
mkdir -p tests
mkdir -p .github/workflows
```

---

### Step 1.2 — Copy All Generated Files

The files were already generated for you. Copy each one into your repo:

**Root level files (copy to repo root):**
- `models.py`
- `case_generator.py`
- `client.py`
- `baseline_agent.py`
- `openenv.yaml`
- `pyproject.toml`
- `README.md`
- `prd.md`
- `skill.md`
- `context.md`
- `prompt.md`
- `GUIDE.md` (this file)

**Server files (copy to `server/` folder):**
- `server/app.py`
- `server/rehab_environment.py`
- `server/requirements.txt`
- `server/Dockerfile`

**Create empty init files:**
```bash
touch __init__.py
touch server/__init__.py
touch tests/__init__.py
```

---

### Step 1.3 — Update Your Username

Open these files and replace `YOUR_USERNAME` and `YOUR_HF_USERNAME`:

**openenv.yaml** — line with `author`:
```yaml
author: aniketaslaliya   # your HF username
```

**README.md** — find and replace all `YOUR_USERNAME`:
```bash
# On Mac/Linux:
sed -i '' 's/YOUR_USERNAME/aniketaslaliya/g' README.md
# On Windows (in PowerShell):
(Get-Content README.md) -replace 'YOUR_USERNAME', 'aniketaslaliya' | Set-Content README.md
```

**baseline_agent.py** — the ENV_BASE_URL default is already localhost, no change needed yet.

---

### Step 1.4 — Verify Your File Structure

```bash
# This command shows your full project tree
find . -not -path "./.git/*" -not -path "./__pycache__/*" \
  -not -name "*.pyc" | sort
```

**Expected output:**
```
.
./__init__.py
./.github/
./.github/workflows/
./.vscode/
./.vscode/settings.json
./GUIDE.md
./README.md
./baseline_agent.py
./case_generator.py
./client.py
./context.md
./models.py
./openenv.yaml
./prompt.md
./prd.md
./pyproject.toml
./server/
./server/__init__.py
./server/app.py
./server/Dockerfile
./server/rehab_environment.py
./server/requirements.txt
./skill.md
./tests/
./tests/__init__.py
```

If any file is missing, create or copy it before continuing.

---

### Step 1.5 — Create PR-1

```bash
# Create a branch for PR-1
git checkout -b phase/1-initial-files

# Stage all files
git add .

# Commit with a clear message
git commit -m "feat: add all initial environment files

- models.py: typed Action, Observation, State (Pydantic v2)
- case_generator.py: seeded procedural inmate/slot generator
- server/rehab_environment.py: full reset/step/state logic
- server/app.py: FastAPI server + hackathon endpoints
- client.py: typed Python client
- baseline_agent.py: OpenAI API baseline script
- openenv.yaml: OpenEnv manifest
- prd.md, skill.md, context.md, prompt.md, GUIDE.md: project docs
- Dockerfile + requirements.txt"

# Push branch
git push origin phase/1-initial-files
```

**Go to GitHub and create a Pull Request:**
- Title: `[PR-1] Initial environment files`
- Description:
```
## What's in this PR
- All core environment files from initial generation
- Project documentation (PRD, skill guide, context, prompts)
- Dockerfile and server configuration

## PR-1 Review Checklist
- [ ] All files present (see GUIDE.md Step 1.4 expected output)
- [ ] openenv.yaml has correct author name
- [ ] README.md has correct username
- [ ] No hardcoded API keys anywhere

## Next: PR-2 will run the environment locally
```

**Merge PR-1 into main after team review.**

```bash
# After merge, sync your local main
git checkout main
git pull origin main
```

---

### Phase 1 Complete Checklist
- [ ] All files copied into repo
- [ ] Username updated in openenv.yaml and README.md
- [ ] File structure verified with find command
- [ ] PR-1 created, reviewed, and merged

---

---

# PHASE 2 — Run Locally and Fix Import Errors
## April 1–2

---

### Step 2.1 — Install Dependencies

```bash
# Always work from repo root
cd YOUR_REPO_NAME

# Install all server dependencies
pip install -r server/requirements.txt

# Verify key packages installed
python -c "import openenv; print('openenv OK')"
python -c "import fastapi; print('fastapi OK')"
python -c "import pydantic; print('pydantic OK')"
```

**If any import fails:**
```bash
pip install openenv-core fastapi uvicorn pydantic httpx openai
```

---

### Step 2.2 — Syntax Check All Python Files

Run this before anything else. It catches typos and missing colons:

```bash
python -m py_compile models.py && echo "models.py OK"
python -m py_compile case_generator.py && echo "case_generator.py OK"
python -m py_compile client.py && echo "client.py OK"
python -m py_compile baseline_agent.py && echo "baseline_agent.py OK"
python -m py_compile server/app.py && echo "server/app.py OK"
python -m py_compile server/rehab_environment.py && echo "rehab_environment.py OK"
```

**Expected output:**
```
models.py OK
case_generator.py OK
client.py OK
baseline_agent.py OK
server/app.py OK
rehab_environment.py OK
```

**If any file fails:**
```
  File "server/app.py", line 45
    return {
           ^
SyntaxError: invalid syntax
```

Open that file in VS Code, go to that line number, and fix the syntax error.
Common causes: missing colon after `def`, unclosed parenthesis, wrong indentation.

---

### Step 2.3 — Start the Server

```bash
# From repo root
uvicorn server.app:app --host 0.0.0.0 --port 8000 --reload
```

**Expected output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12345]
INFO:     Started server process [12346]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**If you see ImportError:**
```
ModuleNotFoundError: No module named 'models'
```

This is the import path problem. Fix it by adding to the top of
`server/rehab_environment.py` and `server/app.py`:

```python
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
```

This line is already in the generated files. If it's missing, add it.

**Keep the server running. Open a NEW terminal for the next steps.**

---

### Step 2.4 — Test the Health Endpoint

Open a new terminal (keep server running in the first one):

```bash
curl http://localhost:8000/health
```

**Expected:**
```json
{"status": "healthy", "environment": "rehab_scheduler", "version": "1.0.0"}
```

**If you get "Connection refused":** Server isn't running. Go back to Step 2.3.

---

### Step 2.5 — Test Reset

```bash
curl -X POST http://localhost:8000/reset \
  -H "Content-Type: application/json" \
  -d '{"task_id": 1, "seed": 42}'
```

**Expected:** A large JSON response starting with:
```json
{
  "done": false,
  "reward": null,
  "inmates": [...],
  "total_inmates": 20,
  ...
}
```

**If you get 422 Unprocessable Entity:**
The request body doesn't match what the server expects.
Check the reset() method signature in `server/rehab_environment.py`.

---

### Step 2.6 — Test Step

```bash
curl -X POST http://localhost:8000/step \
  -H "Content-Type: application/json" \
  -d '{"action_type": "assign_program", "inmate_id": "I-001", "program_type": "therapy"}'
```

**Expected:** JSON with `last_action_result` showing the assignment outcome.

---

### Step 2.7 — Test Submit

```bash
curl -X POST http://localhost:8000/step \
  -H "Content-Type: application/json" \
  -d '{"action_type": "submit_schedule"}'
```

**Expected:** JSON with `done: true` and `reward` as a float between 0 and 1.

---

### Step 2.8 — Stop Server and Create PR-2

Press `Ctrl+C` in the server terminal to stop it.

```bash
git checkout -b phase/2-local-run-verified
git add .
git commit -m "fix: resolve import paths and verify local server runs

- All 6 endpoints respond correctly on localhost:8000
- reset() returns 20 inmates for task_id=1
- step() with assign_program updates risk score
- submit_schedule returns reward in [0, 1]
- All py_compile checks pass"

git push origin phase/2-local-run-verified
```

**PR-2 on GitHub:**
- Title: `[PR-2] Local server verified`
- Description:
```
## What changed
- Fixed any import path issues
- Verified all core endpoints respond correctly

## PR-2 Review Checklist
- [ ] `python -m py_compile` passes for all files
- [ ] Server starts without errors
- [ ] /health returns {"status": "healthy"}
- [ ] /reset with task_id=1 returns 20 inmates
- [ ] /step with assign_program returns updated observation
- [ ] /step with submit_schedule returns reward in [0.0, 1.0]

## Evidence (paste your curl outputs here)
```

**Merge PR-2, then sync main:**
```bash
git checkout main
git pull origin main
```

---

### Phase 2 Complete Checklist
- [ ] All py_compile checks pass
- [ ] Server starts without import errors
- [ ] /health, /reset, /step all return correct responses
- [ ] PR-2 merged

---

---

# PHASE 3 — Test All Hackathon Endpoints
## April 2–3

---

### Step 3.1 — Create a REST Client Test File

Create a file `tests/manual_test.http` for VS Code REST Client extension:

```http
### Health
GET http://localhost:8000/health

###

### List Tasks (hackathon required)
GET http://localhost:8000/tasks

###

### Reset Task 1
POST http://localhost:8000/reset
Content-Type: application/json

{
  "task_id": 1,
  "seed": 42
}

###

### Assign first inmate to therapy
POST http://localhost:8000/step
Content-Type: application/json

{
  "action_type": "assign_program",
  "inmate_id": "I-001",
  "program_type": "therapy"
}

###

### Submit schedule (terminal action)
POST http://localhost:8000/step
Content-Type: application/json

{
  "action_type": "submit_schedule"
}

###

### Get State
GET http://localhost:8000/state

###

### Run Grader (hackathon required)
POST http://localhost:8000/grader
Content-Type: application/json

{
  "task_id": 1,
  "seed": 42
}

###

### Run Baseline (hackathon required)
GET http://localhost:8000/baseline

###

### Reset Task 2
POST http://localhost:8000/reset
Content-Type: application/json

{
  "task_id": 2,
  "seed": 42
}

###

### Reset Task 3
POST http://localhost:8000/reset
Content-Type: application/json

{
  "task_id": 3,
  "seed": 42
}
```

In VS Code, click "Send Request" above each `###` block to test individually.

---

### Step 3.2 — Verify /tasks Response

Start server, then:
```bash
curl http://localhost:8000/tasks | python -m json.tool
```

**Must contain all of these fields or hackathon validation will fail:**
```json
{
  "tasks": [
    {"task_id": 1, "name": "...", "difficulty": "easy", ...},
    {"task_id": 2, "name": "...", "difficulty": "medium", ...},
    {"task_id": 3, "name": "...", "difficulty": "hard", ...}
  ],
  "action_schema": {
    "action_type": {...},
    "inmate_id": {...},
    "program_type": {...}
  }
}
```

---

### Step 3.3 — Verify /grader Response

```bash
curl -X POST http://localhost:8000/grader \
  -H "Content-Type: application/json" \
  -d '{"task_id": 1, "seed": 42}' | python -m json.tool
```

**Must have:**
```json
{
  "task_id": 1,
  "seed": 42,
  "grader_score": 0.6234,
  "steps_taken": 22,
  "violations": 0,
  "assignments": 20,
  "final_avg_risk": 3.41
}
```

**Critical check:** `grader_score` must be between 0.0 and 1.0.
If it's above 1.0 or below 0.0, the grader formula has a bug.

---

### Step 3.4 — Verify /baseline Response

```bash
curl http://localhost:8000/baseline | python -m json.tool
```

**This will take 1–2 minutes — it runs all 3 tasks.**

**Must have scores for all 3 tasks:**
```json
{
  "baseline_agent": "greedy_priority",
  "scores": {
    "task_1": {"grader_score": 0.xx, ...},
    "task_2": {"grader_score": 0.xx, ...},
    "task_3": {"grader_score": 0.xx, ...}
  }
}
```

**Record these scores.** You'll need them for the README.

---

### Step 3.5 — Test All 3 Task Resets

```bash
# Task 1 — should return 20 inmates
curl -s -X POST http://localhost:8000/reset \
  -H "Content-Type: application/json" \
  -d '{"task_id": 1, "seed": 42}' | python -c "
import json,sys
d=json.load(sys.stdin)
print(f'Task 1: {d[\"total_inmates\"]} inmates, slots: {d[\"program_slots\"]}')
"

# Task 2 — should return 50 inmates
curl -s -X POST http://localhost:8000/reset \
  -H "Content-Type: application/json" \
  -d '{"task_id": 2, "seed": 42}' | python -c "
import json,sys
d=json.load(sys.stdin)
print(f'Task 2: {d[\"total_inmates\"]} inmates, slots: {d[\"program_slots\"]}')
"

# Task 3 — should return 180 inmates initially
curl -s -X POST http://localhost:8000/reset \
  -H "Content-Type: application/json" \
  -d '{"task_id": 3, "seed": 42}' | python -c "
import json,sys
d=json.load(sys.stdin)
print(f'Task 3: {d[\"total_inmates\"]} inmates, slots: {d[\"program_slots\"]}')
"
```

---

### Step 3.6 — Create PR-3

```bash
git checkout -b phase/3-endpoints-verified
git add tests/manual_test.http
git commit -m "test: add REST client test file, verify all hackathon endpoints

Endpoint verification results:
- GET /health: OK
- GET /tasks: 3 tasks + action_schema present
- POST /grader: grader_score in [0.0, 1.0]
- GET /baseline: scores for all 3 tasks
- POST /reset task_id=1: 20 inmates
- POST /reset task_id=2: 50 inmates
- POST /reset task_id=3: 180 inmates"

git push origin phase/3-endpoints-verified
```

**PR-3 on GitHub:**
- Title: `[PR-3] All endpoints verified`
- Description: paste actual curl output for each endpoint

**Merge PR-3, sync main.**

---

### Phase 3 Complete Checklist
- [ ] /health responds correctly
- [ ] /tasks has 3 tasks + full action_schema
- [ ] /grader returns score in [0.0, 1.0]
- [ ] /baseline returns scores for all 3 tasks
- [ ] All 3 task resets return correct inmate counts
- [ ] Scores recorded for README
- [ ] PR-3 merged

---

---

# PHASE 4 — Write and Run Tests
## April 3–4

---

### Step 4.1 — Create test_grader.py

Create `tests/test_grader.py`:

```python
"""Unit tests for the grader formula."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from case_generator import generate_task_1, generate_task_2, compute_optimal_score
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
    inmates, slots = generate_task_1(seed=42)
    base_args = dict(
        inmates=inmates,
        wasted_slots=0,
        total_slots=25,
        steps_taken=20,
        max_steps=40,
        optimal_score=0.8,
    )
    score_clean    = _grade(**base_args, violations=0)
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

    # Greedy: assign first inmate to first available slot
    for _ in range(30):
        if obs.done:
            break
        unassigned = [i for i in obs.inmates if i["assigned_program"] is None]
        available  = {k: v for k, v in obs.program_slots.items() if v > 0}
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
    assert obs.reward >= 0.3, f"Expected score >= 0.3, got {obs.reward}"
    assert obs.done is True
```

---

### Step 4.2 — Create test_endpoints.py

Create `tests/test_endpoints.py`:

```python
"""Integration tests for all API endpoints."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from fastapi.testclient import TestClient
from server.app import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "healthy"


def test_tasks_structure():
    r = client.get("/tasks")
    assert r.status_code == 200
    data = r.json()
    assert len(data["tasks"]) == 3
    assert "action_schema" in data
    assert "action_type" in data["action_schema"]
    task_ids = [t["task_id"] for t in data["tasks"]]
    assert task_ids == [1, 2, 3]


def test_reset_task1():
    r = client.post("/reset", json={"task_id": 1, "seed": 42})
    assert r.status_code == 200
    obs = r.json()
    assert obs["total_inmates"] == 20
    assert obs["done"] is False
    assert obs["reward"] is None
    assert len(obs["inmates"]) == 20


def test_reset_task2():
    r = client.post("/reset", json={"task_id": 2, "seed": 42})
    assert r.status_code == 200
    assert r.json()["total_inmates"] == 50


def test_step_assign():
    client.post("/reset", json={"task_id": 1, "seed": 42})
    r = client.post("/step", json={
        "action_type": "assign_program",
        "inmate_id": "I-001",
        "program_type": "therapy"
    })
    assert r.status_code == 200
    obs = r.json()
    assert obs["last_action_valid"] is True
    assert "I-001" in obs["last_action_result"] or "therapy" in obs["last_action_result"]


def test_step_submit_returns_score():
    client.post("/reset", json={"task_id": 1, "seed": 42})
    r = client.post("/step", json={"action_type": "submit_schedule"})
    assert r.status_code == 200
    obs = r.json()
    assert obs["done"] is True
    assert obs["reward"] is not None
    assert 0.0 <= obs["reward"] <= 1.0


def test_grader_endpoint():
    r = client.post("/grader", json={"task_id": 1, "seed": 42})
    assert r.status_code == 200
    data = r.json()
    assert "grader_score" in data
    assert 0.0 <= data["grader_score"] <= 1.0


def test_state_after_steps():
    client.post("/reset", json={"task_id": 1, "seed": 42})
    client.post("/step", json={
        "action_type": "assign_program",
        "inmate_id": "I-001",
        "program_type": "therapy"
    })
    r = client.get("/state")
    assert r.status_code == 200
    state = r.json()
    assert state["step_count"] == 1
    assert state["task_id"] == 1
```

---

### Step 4.3 — Create test_reproducibility.py

Create `tests/test_reproducibility.py`:

```python
"""Reproducibility tests — same seed must always produce same score."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import RehabAction, ActionType
from server.rehab_environment import RehabEnvironment


def run_full_episode(task_id: int, seed: int) -> float:
    """Run a complete episode and return final score."""
    env = RehabEnvironment()
    obs = env.reset(task_id=task_id, seed=seed)
    obs = env.step(RehabAction(action_type=ActionType.SUBMIT_SCHEDULE))
    return obs.reward


def test_same_seed_same_score():
    """Identical seed must produce identical score across 3 runs."""
    scores = [run_full_episode(task_id=1, seed=42) for _ in range(3)]
    assert scores[0] == scores[1] == scores[2], \
        f"Scores differ across runs: {scores}"


def test_different_seeds_different_scores():
    """Different seeds must produce different case populations."""
    score_42 = run_full_episode(task_id=1, seed=42)
    score_99 = run_full_episode(task_id=1, seed=99)
    assert score_42 != score_99, \
        "Seeds 42 and 99 produced identical scores — generator is not seeded correctly"


def test_reproducibility_all_tasks():
    """All 3 tasks must be reproducible."""
    for task_id in [1, 2, 3]:
        s1 = run_full_episode(task_id=task_id, seed=42)
        s2 = run_full_episode(task_id=task_id, seed=42)
        assert s1 == s2, f"Task {task_id} not reproducible: {s1} != {s2}"
```

---

### Step 4.4 — Install pytest and Run Tests

```bash
pip install pytest

# Run all tests
pytest tests/ -v

# Expected output:
# tests/test_grader.py::test_grader_score_in_range PASSED
# tests/test_grader.py::test_grader_violations_reduce_score PASSED
# tests/test_grader.py::test_grader_different_seeds PASSED
# tests/test_grader.py::test_full_episode_score_nonzero PASSED
# tests/test_endpoints.py::test_health PASSED
# tests/test_endpoints.py::test_tasks_structure PASSED
# tests/test_endpoints.py::test_reset_task1 PASSED
# tests/test_endpoints.py::test_reset_task2 PASSED
# tests/test_endpoints.py::test_step_assign PASSED
# tests/test_endpoints.py::test_step_submit_returns_score PASSED
# tests/test_endpoints.py::test_grader_endpoint PASSED
# tests/test_endpoints.py::test_state_after_steps PASSED
# tests/test_reproducibility.py::test_same_seed_same_score PASSED
# tests/test_reproducibility.py::test_different_seeds_different_scores PASSED
# tests/test_reproducibility.py::test_reproducibility_all_tasks PASSED
#
# 15 passed in 12.34s
```

**If any test fails, read the error message carefully.**
The error will tell you exactly which assertion failed and what the actual value was.
Fix the issue in the relevant source file, then re-run tests.

---

### Step 4.5 — Add GitHub Actions CI

Create `.github/workflows/validate.yml`:

```yaml
name: Validate Environment

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: pip install -r server/requirements.txt pytest

      - name: Syntax check all Python files
        run: |
          python -m py_compile models.py
          python -m py_compile case_generator.py
          python -m py_compile client.py
          python -m py_compile baseline_agent.py
          python -m py_compile server/app.py
          python -m py_compile server/rehab_environment.py
          echo "All syntax checks passed"

      - name: Run unit and integration tests
        run: pytest tests/ -v

      - name: Start server and verify /health
        run: |
          uvicorn server.app:app --port 8000 &
          sleep 5
          curl -f http://localhost:8000/health
          curl -f http://localhost:8000/tasks
          echo "Server endpoints verified"
```

---

### Step 4.6 — Create PR-4

```bash
git checkout -b phase/4-tests-and-ci
git add tests/ .github/
git commit -m "test: add unit tests, integration tests, CI pipeline

Tests added:
- test_grader.py: 4 tests for grader formula
- test_endpoints.py: 8 tests for all API endpoints
- test_reproducibility.py: 3 tests for seed reproducibility
- All 15 tests pass locally

CI added:
- .github/workflows/validate.yml
- Runs on every push and PR
- Syntax check + pytest + server startup verification"

git push origin phase/4-tests-and-ci
```

**PR-4 on GitHub:**
- Title: `[PR-4] Tests and CI pipeline`
- Description: paste pytest output showing all 15 tests passing
- Wait for CI to go green before merging

**Merge PR-4, sync main.**

---

### Phase 4 Complete Checklist
- [ ] All 15 tests pass locally with `pytest tests/ -v`
- [ ] GitHub Actions CI is green on the PR
- [ ] PR-4 merged

---

---

# PHASE 5 — Docker Build and Run
## April 4–5

---

### Step 5.1 — Build the Docker Image

```bash
# From repo root
docker build -t rehab-scheduler -f server/Dockerfile .
```

**This will take 2–3 minutes the first time.**

**Expected final output:**
```
Successfully built abc123def456
Successfully tagged rehab-scheduler:latest
```

**If build fails with "COPY failed":**
Check that all file paths in Dockerfile match actual file locations.
The Dockerfile expects files at:
- `models.py` (at root)
- `case_generator.py` (at root)
- `server/` (directory)

---

### Step 5.2 — Run the Docker Container

```bash
docker run -d -p 8001:8000 --name rehab-test rehab-scheduler
```

Flags explained:
- `-d` runs in background
- `-p 8001:8000` maps container port 8000 to your port 8001
  (using 8001 so it doesn't conflict if server.app is still running on 8000)
- `--name rehab-test` gives it a name for easy management

**Wait 5 seconds, then verify:**
```bash
curl http://localhost:8001/health
# {"status": "healthy", ...}

curl http://localhost:8001/tasks
# {tasks: [...]}
```

---

### Step 5.3 — Check Container Logs if Something is Wrong

```bash
docker logs rehab-test
```

**Common Docker errors:**

Error: `ModuleNotFoundError: No module named 'models'`
Fix: Add `ENV PYTHONPATH=/app:/app/server` to Dockerfile

Error: `ModuleNotFoundError: No module named 'openenv'`
Fix: Check requirements.txt has `openenv-core>=0.2.2`

Error: container exits immediately
Fix: `docker logs rehab-test` and read the actual Python traceback

---

### Step 5.4 — Stop and Clean Up

```bash
docker stop rehab-test
docker rm rehab-test
```

---

### Step 5.5 — Create PR-5

```bash
git checkout -b phase/5-docker-verified
# No code changes needed if Docker worked
# Just document the verification
git commit --allow-empty -m "verify: Docker build and run successful

docker build -t rehab-scheduler -f server/Dockerfile . → SUCCESS
docker run -p 8001:8000 rehab-scheduler → SUCCESS
curl http://localhost:8001/health → {status: healthy}
curl http://localhost:8001/tasks → 3 tasks returned
All endpoints respond correctly from Docker container"

git push origin phase/5-docker-verified
```

**PR-5 on GitHub:**
- Title: `[PR-5] Docker verified`
- Description: paste docker build output and curl responses

**Merge PR-5, sync main.**

---

### Phase 5 Complete Checklist
- [ ] `docker build` completes without errors
- [ ] `docker run` starts successfully
- [ ] /health and /tasks respond from Docker container
- [ ] PR-5 merged

---

---

# PHASE 6 — Deploy to HF Spaces
## April 5–6

---

### Step 6.1 — Login to Hugging Face

```bash
huggingface-cli login
# Enter your HF token (starts with hf_...)
# You should have done this in Phase 0
```

---

### Step 6.2 — Deploy

```bash
# From repo root
cd rehab_scheduler  # or whatever your project folder is called

openenv push --repo-id aniketaslaliya/rehab-scheduler
```

**This will:**
1. Create a new HF Space called `rehab-scheduler` under your account
2. Upload all files
3. Build the Docker image on HF infrastructure
4. Start the server

**This takes 3–5 minutes.**

**Expected output:**
```
Pushing environment to Hugging Face Spaces...
Space created: https://huggingface.co/spaces/aniketaslaliya/rehab-scheduler
Building Docker image...
Build complete.
Environment available at: https://aniketaslaliya-rehab-scheduler.hf.space
```

---

### Step 6.3 — Wait for Space to Start

HF Spaces can take 2–5 minutes to start after the first deployment.

Go to: `https://huggingface.co/spaces/aniketaslaliya/rehab-scheduler`

You should see a "Building" status, then "Running".

---

### Step 6.4 — Verify Live Deployment

```bash
export SPACE_URL=https://aniketaslaliya-rehab-scheduler.hf.space

# Test all required endpoints on live URL
curl $SPACE_URL/health
curl $SPACE_URL/tasks
curl -X POST $SPACE_URL/grader \
  -H "Content-Type: application/json" \
  -d '{"task_id": 1, "seed": 42}'
curl $SPACE_URL/baseline
```

**All 4 must return valid JSON. Save the output.**

---

### Step 6.5 — Update README With Live URL

Open `README.md` and update:
```markdown
- [Deployed Space](https://huggingface.co/spaces/aniketaslaliya/rehab-scheduler)
```

Also update `baseline_agent.py` default comment:
```python
ENV_BASE_URL = os.environ.get(
    "REHAB_ENV_URL",
    "https://aniketaslaliya-rehab-scheduler.hf.space"
)
```

---

### Step 6.6 — Create PR-6

```bash
git checkout -b phase/6-deployed-to-hf-spaces
git add README.md baseline_agent.py
git commit -m "deploy: environment live on HF Spaces

Space URL: https://aniketaslaliya-rehab-scheduler.hf.space
All endpoints verified on live URL:
- /health: OK
- /tasks: 3 tasks returned
- /grader: score in [0.0, 1.0]
- /baseline: scores for all 3 tasks

Updated README.md and baseline_agent.py with live URL"

git push origin phase/6-deployed-to-hf-spaces
```

**PR-6 on GitHub:**
- Title: `[PR-6] Deployed to HF Spaces`
- Description: paste live URL and curl outputs from Step 6.4

**Merge PR-6, sync main.**

---

### Phase 6 Complete Checklist
- [ ] `openenv push` completed without errors
- [ ] HF Space shows "Running" status
- [ ] /health, /tasks, /grader, /baseline all work on live URL
- [ ] README updated with live Space URL
- [ ] PR-6 merged

---

---

# PHASE 7 — Run Baseline Agent and Record Scores
## April 6–7

---

### Step 7.1 — Set Environment Variables

```bash
# Mac/Linux
export OPENAI_API_KEY=sk-your-key-here
export REHAB_ENV_URL=https://aniketaslaliya-rehab-scheduler.hf.space

# Windows (PowerShell)
$env:OPENAI_API_KEY="sk-your-key-here"
$env:REHAB_ENV_URL="https://aniketaslaliya-rehab-scheduler.hf.space"
```

---

### Step 7.2 — Run the Baseline Agent

```bash
python baseline_agent.py
```

**Expected output:**
```
Rehabilitation Scheduler — Baseline Agent
Environment: https://aniketaslaliya-rehab-scheduler.hf.space
Model:       gpt-4o

============================================================
Task 1 — starting episode (seed=42)
============================================================
Step   1: {'action_type': 'assign_program', 'inmate_id': 'I-007', ...}
Step   2: {'action_type': 'assign_program', 'inmate_id': 'I-003', ...}
...
Task 1 complete:
  Score:       0.7832
  Assignments: 20
  Violations:  0
  Risk:        5.61 → 2.43

============================================================
Task 2 — starting episode (seed=42)
...
Task 2 complete:
  Score:       0.5914

============================================================
Task 3 — starting episode (seed=42)
...
Task 3 complete:
  Score:       0.4127

============================================================
BASELINE RESULTS SUMMARY
============================================================
  task_1: 0.7832
  task_2: 0.5914
  task_3: 0.4127

Results saved to baseline_results.json
```

---

### Step 7.3 — Run It 3 Times, Verify Same Scores

```bash
python baseline_agent.py > run1.txt
python baseline_agent.py > run2.txt
python baseline_agent.py > run3.txt

# Compare the summary lines
grep "task_" run1.txt run2.txt run3.txt
```

**All 3 runs must show identical scores.**
If they differ, the seed is not propagating correctly.

---

### Step 7.4 — Update README With Actual Scores

Open `README.md` and fill in the Baseline Scores table with your actual numbers:

```markdown
## Baseline Scores

| Task | Difficulty | Baseline (GPT-4o greedy) |
|---|---|---|
| 1 | Easy | 0.7832 |
| 2 | Medium | 0.5914 |
| 3 | Hard | 0.4127 |
```

---

### Step 7.5 — Create PR-7

```bash
git checkout -b phase/7-baseline-scores-recorded
git add baseline_results.json README.md run1.txt run2.txt run3.txt
git commit -m "feat: record baseline agent scores

GPT-4o greedy baseline on all 3 tasks (seed=42):
- Task 1 (easy):   0.7832
- Task 2 (medium): 0.5914
- Task 3 (hard):   0.4127

Verified reproducible across 3 independent runs.
baseline_results.json saved and committed.
README.md updated with baseline scores."

git push origin phase/7-baseline-scores-recorded
```

**PR-7 on GitHub:**
- Title: `[PR-7] Baseline scores recorded`
- Description: paste all 3 run outputs showing identical scores

**Merge PR-7, sync main.**

---

### Phase 7 Complete Checklist
- [ ] `python baseline_agent.py` runs without errors
- [ ] 3 identical runs verified
- [ ] `baseline_results.json` committed to repo
- [ ] README updated with actual scores
- [ ] PR-7 merged

---

---

# PHASE 8 — Final Validation and Submit
## April 7–8 (Submit Before 11:59 PM IST April 8)

---

### Step 8.1 — Run openenv validate

```bash
openenv validate --verbose
```

**Expected output:**
```
Checking openenv.yaml... OK
Checking required files... OK
Checking Dockerfile... OK
Checking /health endpoint... OK
Checking /tasks endpoint... OK
Checking /reset endpoint... OK
Checking /step endpoint... OK
Checking /state endpoint... OK

Validation passed.
```

**If any check fails, fix it immediately.**
Do not submit until `openenv validate` passes completely.

---

### Step 8.2 — Final Pre-Submission Checklist

Go through every item in `prd.md` Section 10:

```bash
SPACE_URL=https://aniketaslaliya-rehab-scheduler.hf.space

# 1. Health check
curl -f $SPACE_URL/health
echo "✅ Health OK"

# 2. Tasks endpoint
curl -f $SPACE_URL/tasks | python -c "
import json,sys
d=json.load(sys.stdin)
assert len(d['tasks'])==3
assert 'action_schema' in d
print('✅ Tasks OK — 3 tasks + action_schema present')
"

# 3. Reset works
curl -f -X POST $SPACE_URL/reset \
  -H "Content-Type: application/json" \
  -d '{"task_id": 1, "seed": 42}' | python -c "
import json,sys
d=json.load(sys.stdin)
assert d['total_inmates']==20
assert d['done']==False
print('✅ Reset OK — 20 inmates returned')
"

# 4. Submit returns score
curl -f -X POST $SPACE_URL/reset \
  -H "Content-Type: application/json" \
  -d '{"task_id": 1, "seed": 42}' > /dev/null
curl -f -X POST $SPACE_URL/step \
  -H "Content-Type: application/json" \
  -d '{"action_type": "submit_schedule"}' | python -c "
import json,sys
d=json.load(sys.stdin)
assert d['done']==True
assert 0.0 <= d['reward'] <= 1.0
print(f'✅ Submit OK — reward={d[\"reward\"]}')
"

# 5. Grader endpoint
curl -f -X POST $SPACE_URL/grader \
  -H "Content-Type: application/json" \
  -d '{"task_id": 1, "seed": 42}' | python -c "
import json,sys
d=json.load(sys.stdin)
assert 0.0 <= d['grader_score'] <= 1.0
print(f'✅ Grader OK — score={d[\"grader_score\"]}')
"

# 6. Baseline endpoint
curl -f $SPACE_URL/baseline | python -c "
import json,sys
d=json.load(sys.stdin)
assert 'task_1' in d['scores']
assert 'task_2' in d['scores']
assert 'task_3' in d['scores']
print('✅ Baseline OK — all 3 task scores present')
"

echo ""
echo "All checks passed. Ready to submit."
```

---

### Step 8.3 — Final Commit

```bash
git checkout -b phase/8-final-submission

# Make sure baseline_results.json is committed
git add baseline_results.json README.md

git commit -m "chore: final submission preparation

Pre-submission checklist:
✅ openenv validate passes
✅ /health responds
✅ /tasks returns 3 tasks + action_schema
✅ /reset returns correct observations
✅ /step submit_schedule returns reward in [0, 1]
✅ /grader returns score in [0, 1]
✅ /baseline returns scores for all 3 tasks
✅ docker build + run verified
✅ baseline agent reproducible (3 identical runs)
✅ README complete with baseline scores
✅ baseline_results.json committed

Space URL: https://aniketaslaliya-rehab-scheduler.hf.space"

git push origin phase/8-final-submission
```

**Create PR-8:**
- Title: `[PR-8] Final submission — all validation checks passed`
- Description: paste full output from Step 8.2 showing all ✅
- Merge immediately

---

### Step 8.4 — Submit

Go to the hackathon platform and paste your HF Space URL:
```
https://huggingface.co/spaces/aniketaslaliya/rehab-scheduler
```

**Submit before April 8, 11:59 PM IST.**

---

### Phase 8 Complete Checklist
- [ ] `openenv validate --verbose` passes
- [ ] All 6 pre-submission curl checks pass
- [ ] PR-8 merged
- [ ] URL submitted on hackathon platform
- [ ] Screenshot of submission taken as proof

---

---

## PR Summary — All 8 Pull Requests

| PR | Branch | Purpose | Merge condition |
|---|---|---|---|
| PR-1 | phase/1-initial-files | Copy all generated files | All files present |
| PR-2 | phase/2-local-run-verified | Server runs locally | All curl outputs correct |
| PR-3 | phase/3-endpoints-verified | All endpoints tested | /tasks, /grader, /baseline work |
| PR-4 | phase/4-tests-and-ci | Tests + GitHub Actions | All 15 tests green, CI green |
| PR-5 | phase/5-docker-verified | Docker works | Build + run + health check pass |
| PR-6 | phase/6-deployed-to-hf-spaces | Live on HF Spaces | All endpoints live |
| PR-7 | phase/7-baseline-scores-recorded | Baseline scores | 3 identical runs verified |
| PR-8 | phase/8-final-submission | Final checks | All ✅, submitted |

---

## Emergency Fixes

### "I'm getting an error I can't understand"

1. Copy the full error message
2. Open `prompt.md`
3. Find the matching debugging prompt in Section 1
4. Open a new chat with Claude or Copilot
5. Paste `context.md` first, then the debugging prompt with your error

### "I missed a step and now things are broken"

Do NOT try to fix everything at once. Go back to the last phase that worked
and redo from there. The phases are designed to be checkpoints.

### "The HF Space keeps timing out"

HF Spaces free tier sleeps after 48 hours of inactivity.
Visit the Space URL in your browser to wake it up before running any tests.

### "openenv validate is failing with an error I don't understand"

```bash
# Check what version you have
pip show openenv-core

# Try reinstalling
pip install --force-reinstall openenv-core==0.2.2

# Run validate with maximum verbosity
openenv validate --verbose 2>&1 | tee validate_output.txt
cat validate_output.txt
```

### "Docker build fails with no space left on device"

```bash
# Clean up unused Docker images
docker system prune -a
# Try build again
docker build -t rehab-scheduler -f server/Dockerfile .
```

---

## Team Responsibility Split

| Phase | Lead | Support |
|---|---|---|
| 0 — Setup | All | All |
| 1 — Copy files | Aniket | — |
| 2 — Local run | Aniket | Aditya (debug) |
| 3 — Endpoint testing | Mitali | Aniket |
| 4 — Tests + CI | Mitali | Aditya |
| 5 — Docker | Aditya | Aniket |
| 6 — HF Deploy | Aditya | Aniket |
| 7 — Baseline | Mitali | — |
| 8 — Final submit | Aniket | All |
