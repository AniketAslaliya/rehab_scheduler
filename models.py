"""
Rehabilitation Scheduler — Typed Models
All Action, Observation, and State types for the environment.
"""

from typing import List, Optional, Dict, Any
from enum import Enum
from openenv.core.env_server import Action, Observation, State


# ─────────────────────────────────────────────
# Enums
# ─────────────────────────────────────────────

class ProgramType(str, Enum):
    EDUCATION       = "education"         # literacy, GED, vocational
    THERAPY         = "therapy"           # counselling, group therapy
    VOCATIONAL      = "vocational"        # job skills, trade training
    SUBSTANCE_ABUSE = "substance_abuse"   # drug/alcohol rehabilitation
    ANGER_MGMT      = "anger_mgmt"        # anger management sessions


class ActionType(str, Enum):
    ASSIGN_PROGRAM    = "assign_program"    # assign inmate to a program
    RESCHEDULE        = "reschedule"        # move inmate to different slot/program
    HANDLE_DROPOUT    = "handle_dropout"    # fill a vacated slot from waitlist
    ESCALATE_CASE     = "escalate_case"     # flag for individual counsellor review
    REALLOCATE_BUDGET = "reallocate_budget" # shift resources between program types
    SUBMIT_SCHEDULE   = "submit_schedule"   # terminal — end episode, trigger grader


class RiskLevel(str, Enum):
    LOW    = "low"     # risk score 0–3
    MEDIUM = "medium"  # risk score 4–6
    HIGH   = "high"    # risk score 7–10


# ─────────────────────────────────────────────
# Core data objects (NOT Pydantic — plain dataclasses
# used internally by environment logic)
# ─────────────────────────────────────────────

class InmateProfile:
    """Internal representation of one inmate."""
    def __init__(
        self,
        inmate_id: str,
        age: int,
        offence_category: str,    # e.g. "drug", "violent", "property", "fraud"
        risk_score: float,        # 0.0–10.0, lower is better
        receptivity: float,       # 0.0–1.0 — how responsive to programs
        conflict_with: List[str], # list of inmate_ids they cannot share sessions with
        refused_programs: List[ProgramType],  # programs this inmate has refused
        assigned_program: Optional[ProgramType] = None,
        is_escalated: bool = False,
        dropout_count: int = 0,
    ):
        self.inmate_id       = inmate_id
        self.age             = age
        self.offence_category = offence_category
        self.risk_score      = risk_score
        self.initial_risk    = risk_score  # saved for grader
        self.receptivity     = receptivity
        self.conflict_with   = conflict_with
        self.refused_programs = refused_programs
        self.assigned_program = assigned_program
        self.is_escalated    = is_escalated
        self.dropout_count   = dropout_count

    def to_dict(self) -> Dict[str, Any]:
        return {
            "inmate_id":        self.inmate_id,
            "age":              self.age,
            "offence_category": self.offence_category,
            "risk_score":       round(self.risk_score, 3),
            "risk_level":       self._risk_level(),
            "receptivity":      round(self.receptivity, 3),
            "conflict_with":    self.conflict_with,
            "refused_programs": [p.value for p in self.refused_programs],
            "assigned_program": self.assigned_program.value if self.assigned_program else None,
            "is_escalated":     self.is_escalated,
            "dropout_count":    self.dropout_count,
        }

    def _risk_level(self) -> str:
        if self.risk_score <= 3.0:
            return RiskLevel.LOW.value
        elif self.risk_score <= 6.0:
            return RiskLevel.MEDIUM.value
        return RiskLevel.HIGH.value


# ─────────────────────────────────────────────
# Pydantic Action — what the agent sends each step
# ─────────────────────────────────────────────

class RehabAction(Action):
    """
    One agent action per step.

    Examples
    --------
    Assign:
        {"action_type": "assign_program",
         "inmate_id": "I-003",
         "program_type": "therapy"}

    Reschedule:
        {"action_type": "reschedule",
         "inmate_id": "I-007",
         "program_type": "vocational"}

    Handle dropout:
        {"action_type": "handle_dropout",
         "inmate_id": "I-012",        # the dropout
         "replacement_id": "I-019"}   # pulled from waitlist

    Escalate:
        {"action_type": "escalate_case",
         "inmate_id": "I-005"}

    Reallocate budget:
        {"action_type": "reallocate_budget",
         "from_program": "education",
         "to_program": "therapy",
         "slots": 2}

    Submit (terminal):
        {"action_type": "submit_schedule"}
    """
    action_type:     ActionType
    inmate_id:       Optional[str]         = None
    program_type:    Optional[ProgramType] = None
    replacement_id:  Optional[str]         = None  # for handle_dropout
    from_program:    Optional[ProgramType] = None  # for reallocate_budget
    to_program:      Optional[ProgramType] = None  # for reallocate_budget
    slots:           Optional[int]         = None  # for reallocate_budget


# ─────────────────────────────────────────────
# Pydantic Observation — what the agent receives each step
# ─────────────────────────────────────────────

class RehabObservation(Observation):
    """
    Full environment state visible to the agent after each action.

    Inherits from Observation:
        done:   bool
        reward: Optional[float]
    """
    # Current population snapshot
    inmates:              List[Dict[str, Any]]  # list of InmateProfile.to_dict()
    total_inmates:        int
    assigned_count:       int
    unassigned_count:     int
    escalated_count:      int

    # Program slot availability
    program_slots:        Dict[str, int]   # program_type → available slots
    program_capacity:     Dict[str, int]   # program_type → total capacity

    # Waitlist (unassigned, high-priority)
    waitlist:             List[str]        # inmate_ids waiting for a slot

    # Episode metrics
    avg_risk_score:       float            # current population average
    risk_reduction_so_far: float           # vs episode start (0.0–1.0)
    constraint_violations: int             # conflict violations triggered
    wasted_slots:         int              # slots that could have been filled

    # Feedback from last action
    last_action_result:   str              # human-readable outcome
    last_action_valid:    bool             # was the action legal?
    last_action_penalty:  float            # penalty applied if any

    # Task metadata
    task_id:              int              # 1 = easy, 2 = medium, 3 = hard
    budget_remaining:     Dict[str, int]   # per-program budget (for task 3)
    steps_remaining:      int              # steps before forced termination


# ─────────────────────────────────────────────
# Pydantic State — episode metadata
# ─────────────────────────────────────────────

class RehabState(State):
    """
    Episode-level metadata.

    Inherits from State:
        episode_id:  Optional[str]
        step_count:  int
    """
    task_id:                int
    total_inmates:          int
    initial_avg_risk:       float
    current_avg_risk:       float
    total_assignments:      int
    total_violations:       int
    total_escalations:      int
    budget_cuts_applied:    int            # for task 3
    grader_score:           Optional[float] = None  # filled after SUBMIT_SCHEDULE
