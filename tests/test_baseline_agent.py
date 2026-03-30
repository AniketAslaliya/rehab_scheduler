"""Tests for the deterministic baseline agent."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from baseline_agent import choose_action


def test_choose_action_returns_assignment_when_slots_exist():
    obs = {
        "inmates": [
            {
                "inmate_id": "I-001",
                "risk_score": 9.0,
                "receptivity": 0.8,
                "offence_category": "drug",
                "conflict_with": [],
                "refused_programs": [],
                "assigned_program": None,
            }
        ],
        "program_slots": {"therapy": 1, "substance_abuse": 1},
    }

    action = choose_action(obs)

    assert action["action_type"] == "assign_program"
    assert action["inmate_id"] == "I-001"
    assert action["program_type"] in {"therapy", "substance_abuse"}


def test_choose_action_submits_when_no_legal_assignment_exists():
    obs = {
        "inmates": [
            {
                "inmate_id": "I-001",
                "risk_score": 9.0,
                "receptivity": 0.8,
                "offence_category": "drug",
                "conflict_with": [],
                "refused_programs": ["therapy", "substance_abuse"],
                "assigned_program": None,
            }
        ],
        "program_slots": {"therapy": 1, "substance_abuse": 1},
    }

    action = choose_action(obs)

    assert action == {"action_type": "submit_schedule"}
