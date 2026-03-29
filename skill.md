# SKILL.md — OpenEnv Environment Engineering
## Reference guide for building this project correctly

---

## 1. OpenEnv Core Concepts

### The 3-Method Contract
Every OpenEnv environment MUST implement exactly these:

```python
def reset(self, **kwargs) -> YourObservation:
    """Start new episode. Return initial observation."""

def step(self, action: YourAction, **kwargs) -> YourObservation:
    """Process one action. Return updated observation."""

@property
def state(self) -> YourState:
    """Return current episode metadata."""
```

### Inheritance Chain
```python
# Always inherit from these exact base classes
from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import State
from openenv.core.env_server import Action, Observation

class YourAction(Action):       # Pydantic BaseModel
    your_field: str

class YourObservation(Observation):  # Pydantic BaseModel — has done, reward built in
    your_field: str

class YourState(State):         # Pydantic BaseModel — has episode_id, step_count built in
    your_field: str

class YourEnvironment(Environment):  # Must set SUPPORTS_CONCURRENT_SESSIONS
    SUPPORTS_CONCURRENT_SESSIONS = True
```

### What Observation Already Has (Do NOT redefine)
```python
class Observation(BaseModel):
    done:   bool
    reward: Optional[float]
```

### What State Already Has (Do NOT redefine)
```python
class State(BaseModel):
    episode_id: Optional[str]
    step_count: int
```

---

## 2. FastAPI Wiring

### The One-Line App Creation
```python
# server/app.py
from openenv.core.env_server import create_fastapi_app
from rehab_environment import RehabEnvironment
from models import RehabAction, RehabObservation

app = create_fastapi_app(RehabEnvironment, RehabAction, RehabObservation)
```

This auto-creates: `/ws`, `/reset`, `/step`, `/state`, `/health`, `/web`, `/docs`

### Adding Extra Endpoints (hackathon requires /tasks, /grader, /baseline)
```python
# Add AFTER create_fastapi_app
@app.get("/tasks")
async def list_tasks():
    return {...}

@app.post("/grader")
async def run_grader(request: SomeRequest):
    return {...}
```

---

## 3. Pydantic v2 Patterns (NOT v1)

### Correct model serialization
```python
# v2 — CORRECT
action.model_dump()
action.model_dump(exclude_none=True)

# v1 — WRONG, will break
action.dict()
```

### Correct model validation
```python
# v2 — CORRECT
MyModel.model_validate({"field": "value"})

# v1 — WRONG
MyModel.parse_obj({"field": "value"})
```

### Optional fields
```python
from typing import Optional
class RehabAction(Action):
    inmate_id: Optional[str] = None   # Always provide default for Optional
```

### Enums in Pydantic v2
```python
from enum import Enum
class ProgramType(str, Enum):
    THERAPY = "therapy"

# Access value
program = ProgramType.THERAPY
program.value  # "therapy"
str(program)   # "ProgramType.THERAPY" — NOT what you want
program.value  # always use .value for string output
```

---

## 4. Seeded Randomness (Critical for Reproducibility)

### Always use instance-level Random, never global
```python
# CORRECT — reproducible
class RehabEnvironment(Environment):
    def reset(self, seed: int = 42, **kwargs):
        self._rng = random.Random(seed)
        # use self._rng everywhere inside this instance

# WRONG — breaks reproducibility
import random
random.shuffle(inmates)  # global state contaminates other instances
```

### Pass rng through your generator
```python
def generate_task_1(seed: int = 42):
    rng = random.Random(seed)
    inmates = [make_inmate(i, rng) for i in range(20)]
    return inmates
```

---

## 5. Import Path Management

### The sys.path problem in Docker
When `server/app.py` imports from `models.py` (one level up), Python
can't find it without path manipulation:

```python
# Top of server/rehab_environment.py and server/app.py
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Now this works:
from models import RehabAction, RehabObservation
from case_generator import generate_task_1
```

### In Dockerfile, set PYTHONPATH
```dockerfile
ENV PYTHONPATH=/app:/app/server
```

---

## 6. Running Locally (All Methods)

### Method 1 — uvicorn direct (fastest for development)
```bash
cd rehab_scheduler
pip install -r server/requirements.txt
uvicorn server.app:app --host 0.0.0.0 --port 8000 --reload
```

### Method 2 — uv (recommended by OpenEnv)
```bash
pip install uv
uv sync
uv run server
```

### Method 3 — Docker (test before deploying)
```bash
docker build -t rehab-scheduler -f server/Dockerfile .
docker run -p 8000:8000 rehab-scheduler
```

### Verify it's running
```bash
curl http://localhost:8000/health
curl http://localhost:8000/tasks
curl -X POST http://localhost:8000/reset \
  -H "Content-Type: application/json" \
  -d '{"task_id": 1, "seed": 42}'
```

---

## 7. Deployment to HF Spaces

### One-command deploy
```bash
cd rehab_scheduler
huggingface-cli login   # paste your HF token
openenv push --repo-id YOUR_HF_USERNAME/rehab-scheduler
```

### Verify live deployment
```bash
export SPACE_URL=https://YOUR_USERNAME-rehab-scheduler.hf.space
curl $SPACE_URL/health
curl $SPACE_URL/tasks
curl -X GET $SPACE_URL/baseline
```

### Space URL pattern
HF Spaces URL format: `https://{username}-{space-name}.hf.space`
Dashes replace underscores: `rehab_scheduler` → `rehab-scheduler`

---

## 8. OpenEnv CLI Commands

```bash
# Scaffold new environment
openenv init rehab_scheduler

# Build Docker image
openenv build

# Validate before submission (run this daily)
openenv validate --verbose

# Deploy to HF Spaces
openenv push --repo-id username/rehab-scheduler

# Push with web interface enabled
openenv push --repo-id username/rehab-scheduler --enable-interface
```

---

## 9. Common Errors and Fixes

### Error: `ImportError: cannot import name 'Action' from 'openenv.core.env_server'`
```bash
pip install --upgrade openenv-core
# Check version
python -c "import openenv; print(openenv.__version__)"
```

### Error: `pydantic.errors.PydanticUserError: A non-annotated attribute was detected`
```python
# WRONG — missing type annotation
class RehabAction(Action):
    inmate_id = None

# CORRECT
class RehabAction(Action):
    inmate_id: Optional[str] = None
```

### Error: `422 Unprocessable Entity` on POST /step
The action JSON doesn't match the model. Check:
- Enum values are lowercase strings ("therapy" not "THERAPY")
- No extra fields that aren't in the model
- Required fields are present

### Error: Docker can't find models.py
Add to Dockerfile:
```dockerfile
ENV PYTHONPATH=/app:/app/server
COPY models.py ./models.py
COPY case_generator.py ./case_generator.py
```

### Error: `openenv validate` fails — "missing /tasks endpoint"
Add the endpoint manually to app.py after `create_fastapi_app()`

### Error: Grader returns same score every time
Check that `seed` parameter flows through to `random.Random(seed)`.
Different seeds must produce different populations.

---

## 10. Testing Checklist (Run Before Every Commit)

```bash
# 1. Syntax check all Python files
python -m py_compile models.py
python -m py_compile case_generator.py
python -m py_compile server/rehab_environment.py
python -m py_compile server/app.py
python -m py_compile client.py
python -m py_compile baseline_agent.py

# 2. Start server
uvicorn server.app:app --port 8000 &
sleep 3

# 3. Test all endpoints
curl -s http://localhost:8000/health | python -m json.tool
curl -s http://localhost:8000/tasks | python -m json.tool
curl -s -X POST http://localhost:8000/reset \
  -H "Content-Type: application/json" \
  -d '{"task_id": 1, "seed": 42}' | python -m json.tool
curl -s -X POST http://localhost:8000/step \
  -H "Content-Type: application/json" \
  -d '{"action_type": "submit_schedule"}' | python -m json.tool
curl -s http://localhost:8000/baseline | python -m json.tool

# 4. Docker build
docker build -t rehab-test -f server/Dockerfile .
docker run -d -p 8001:8000 rehab-test
sleep 5
curl -s http://localhost:8001/health

# 5. OpenEnv validate
openenv validate --verbose

# Kill background server
pkill -f "uvicorn server.app"
```

---

## 11. File Ownership Map

| File | Who edits it | Never touch |
|---|---|---|
| `models.py` | Aniket | After April 3 — types are contract |
| `case_generator.py` | Aniket | Seeds after baseline is recorded |
| `server/rehab_environment.py` | Aniket | — |
| `server/app.py` | Mitali | create_fastapi_app() call |
| `baseline_agent.py` | Mitali | SYSTEM_PROMPT after scores recorded |
| `server/Dockerfile` | Aditya | — |
| `openenv.yaml` | Aditya | After deploy |
| `README.md` | Mitali | — |
| `client.py` | Aniket | — |
