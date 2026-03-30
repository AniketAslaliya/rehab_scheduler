"""Integration tests for all API endpoints."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
    r = client.post(
        "/step",
        json={
            "action_type": "assign_program",
            "inmate_id": "I-001",
            "program_type": "therapy",
        },
    )
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


def test_baseline_endpoint():
    r = client.get("/baseline")
    assert r.status_code == 200
    data = r.json()
    assert data["baseline_agent"] == "deterministic_greedy_affinity"
    assert set(data["scores"].keys()) == {"task_1", "task_2", "task_3"}


def test_state_after_steps():
    client.post("/reset", json={"task_id": 1, "seed": 42})
    client.post(
        "/step",
        json={
            "action_type": "assign_program",
            "inmate_id": "I-001",
            "program_type": "therapy",
        },
    )
    r = client.get("/state")
    assert r.status_code == 200
    state = r.json()
    assert state["step_count"] == 1
    assert state["task_id"] == 1
