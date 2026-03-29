"""
Rehabilitation Scheduler — Environment Logic
Implements the OpenEnv Environment interface.
reset() / step() / state property
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from uuid import uuid4
from typing import List, Dict, Optional, Tuple
import random

from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import State

from models import (
    RehabAction, RehabObservation, RehabState,
    ActionType, ProgramType, InmateProfile,
)
from case_generator import (
    generate_task_1, generate_task_2, generate_task_3,
    compute_risk_reduction, compute_optimal_score,
    PROGRAM_EFFECTIVENESS,
)


# ─────────────────────────────────────────────
# Grader functions — one per task
# ─────────────────────────────────────────────

def _grade(
    inmates: List[InmateProfile],
    violations: int,
    wasted_slots: int,
    total_slots: int,
    steps_taken: int,
    max_steps: int,
    optimal_score: float,
) -> float:
    """
    Universal grader formula.
    Score components:
      60% — recidivism reduction vs oracle optimal
      20% — efficiency (steps used, violations, waste)
      20% — slot utilization (filled / total)
    Returns float in [0.0, 1.0].
    """
    # 1. Recidivism reduction component
    total_initial = sum(i.initial_risk for i in inmates)
    total_final   = sum(i.risk_score   for i in inmates)
    actual_reduction = max(0.0, total_initial - total_final)
    max_reduction    = total_initial * optimal_score if optimal_score > 0 else 1.0
    reduction_score  = min(actual_reduction / max(max_reduction, 1e-6), 1.0)

    # 2. Efficiency component
    violation_penalty = min(violations * 0.05, 0.3)
    step_ratio        = steps_taken / max(max_steps, 1)
    efficiency_score  = max(0.0, 1.0 - violation_penalty - (step_ratio * 0.2))

    # 3. Slot utilization
    assigned_count = sum(1 for i in inmates if i.assigned_program is not None)
    utilization    = assigned_count / max(total_slots, 1)

    final = (
        0.60 * reduction_score +
        0.20 * efficiency_score +
        0.20 * utilization
    )
    return round(min(max(final, 0.0), 1.0), 4)


# ─────────────────────────────────────────────
# Main Environment class
# ─────────────────────────────────────────────

class RehabEnvironment(Environment):
    """
    Prison Rehabilitation Program Scheduler.

    The agent acts as an automated program director:
    - Assigns inmates to programs to reduce recidivism risk
    - Handles dropouts, conflicts, escalations, and budget changes
    - Optimizes for maximum risk reduction across the population

    3 tasks of increasing difficulty:
      Task 1 (easy):   20 inmates, sufficient slots, no constraints
      Task 2 (medium): 50 inmates, 60% capacity, conflicts, refusals
      Task 3 (hard):   200 inmates, dynamic arrivals, mid-episode budget cut
    """

    SUPPORTS_CONCURRENT_SESSIONS = True

    MAX_STEPS = {1: 40, 2: 80, 3: 200}

    def __init__(self):
        self._state         = RehabState(
            episode_id=None, step_count=0,
            task_id=1, total_inmates=0,
            initial_avg_risk=0.0, current_avg_risk=0.0,
            total_assignments=0, total_violations=0,
            total_escalations=0, budget_cuts_applied=0,
        )
        self._inmates:       List[InmateProfile]    = []
        self._dynamic_pool:  List[InmateProfile]    = []  # task 3 arrivals
        self._slots:         Dict[ProgramType, int] = {}
        self._capacity:      Dict[ProgramType, int] = {}
        self._violations:    int = 0
        self._wasted_slots:  int = 0
        self._budget_cut:    bool = False
        self._optimal_score: float = 1.0
        self._task_id:       int = 1
        self._done:          bool = False
        self._rng:           random.Random = random.Random(42)

    # ──────────────────────────────
    # reset()
    # ──────────────────────────────

    def reset(self, task_id: int = 1, seed: int = 42, **kwargs) -> RehabObservation:
        """
        Start a new episode.

        Parameters
        ----------
        task_id : int
            1 = easy, 2 = medium, 3 = hard
        seed : int
            Random seed for reproducibility
        """
        self._task_id    = max(1, min(3, int(task_id)))
        self._rng        = random.Random(seed)
        self._violations = 0
        self._wasted_slots = 0
        self._budget_cut = False
        self._done       = False
        self._dynamic_pool = []

        # Generate population
        if self._task_id == 1:
            self._inmates, self._slots = generate_task_1(seed)
        elif self._task_id == 2:
            self._inmates, self._slots = generate_task_2(seed)
        else:
            all_inmates, self._slots = generate_task_3(seed)
            # Split into initial + dynamic arrival pool
            self._inmates      = all_inmates[:180]
            self._dynamic_pool = all_inmates[180:]

        self._capacity = dict(self._slots)

        # Compute oracle optimal for grader normalization
        self._optimal_score = compute_optimal_score(self._inmates, self._slots)

        # Episode state
        avg_risk = self._avg_risk()
        self._state = RehabState(
            episode_id=str(uuid4()),
            step_count=0,
            task_id=self._task_id,
            total_inmates=len(self._inmates),
            initial_avg_risk=round(avg_risk, 3),
            current_avg_risk=round(avg_risk, 3),
            total_assignments=0,
            total_violations=0,
            total_escalations=0,
            budget_cuts_applied=0,
        )

        return self._make_observation(
            last_result="Episode started. Assign programs to reduce recidivism.",
            last_valid=True,
            last_penalty=0.0,
            reward=None,
            done=False,
        )

    # ──────────────────────────────
    # step()
    # ──────────────────────────────

    def step(self, action: RehabAction, **kwargs) -> RehabObservation:
        if self._done:
            return self._make_observation(
                "Episode already ended. Call reset().",
                False, 0.0, 0.0, True,
            )

        self._state.step_count += 1

        # ── Dynamic arrivals (task 3 only) ──
        if self._task_id == 3:
            self._maybe_add_arrivals()
            self._maybe_apply_budget_cut()

        # ── Dispatch action ──
        handler = {
            ActionType.ASSIGN_PROGRAM:    self._handle_assign,
            ActionType.RESCHEDULE:        self._handle_reschedule,
            ActionType.HANDLE_DROPOUT:    self._handle_dropout,
            ActionType.ESCALATE_CASE:     self._handle_escalate,
            ActionType.REALLOCATE_BUDGET: self._handle_reallocate,
            ActionType.SUBMIT_SCHEDULE:   self._handle_submit,
        }.get(action.action_type)

        if handler is None:
            return self._make_observation(
                f"Unknown action type: {action.action_type}",
                False, -0.1, 0.0, False,
            )

        result, valid, penalty, reward, done = handler(action)
        self._done = done

        # Update state metrics
        self._state.current_avg_risk     = round(self._avg_risk(), 3)
        self._state.total_assignments    = sum(1 for i in self._inmates if i.assigned_program)
        self._state.total_violations     = self._violations
        self._state.total_escalations    = sum(1 for i in self._inmates if i.is_escalated)

        # Force termination if max steps reached
        if self._state.step_count >= self.MAX_STEPS[self._task_id] and not done:
            done = True
            self._done = True
            reward = self._compute_final_reward()
            result += f" | Max steps reached. Final score: {reward:.3f}"

        return self._make_observation(result, valid, penalty, reward, done)

    # ──────────────────────────────
    # Action handlers
    # ──────────────────────────────

    def _handle_assign(self, action: RehabAction) -> Tuple:
        inmate = self._find_inmate(action.inmate_id)
        if inmate is None:
            return f"Inmate {action.inmate_id} not found.", False, -0.1, 0.0, False

        if inmate.assigned_program is not None:
            return (
                f"{action.inmate_id} already assigned to "
                f"{inmate.assigned_program.value}. Use reschedule.",
                False, -0.05, 0.0, False,
            )

        program = action.program_type
        if program is None:
            return "program_type required for assign_program.", False, -0.1, 0.0, False

        if program in inmate.refused_programs:
            return (
                f"{action.inmate_id} has refused {program.value}.",
                False, -0.1, 0.0, False,
            )

        if self._slots.get(program, 0) <= 0:
            return f"No slots available in {program.value}.", False, -0.05, 0.0, False

        # Check conflicts
        violation = self._check_conflict(inmate, program)
        if violation:
            self._violations += 1
            self._state.total_violations += 1
            return (
                f"Conflict violation: {action.inmate_id} and {violation} "
                f"cannot share {program.value}.",
                False, -0.15, 0.0, False,
            )

        # Assign
        inmate.assigned_program = program
        self._slots[program] -= 1

        reduction = compute_risk_reduction(inmate, program)
        inmate.risk_score = round(max(0.0, inmate.risk_score - reduction), 3)

        # Step reward proportional to risk reduction
        step_reward = round(reduction / 10.0, 4)

        return (
            f"Assigned {action.inmate_id} to {program.value}. "
            f"Risk reduced by {reduction:.2f} → {inmate.risk_score:.2f}.",
            True, 0.0, step_reward, False,
        )

    def _handle_reschedule(self, action: RehabAction) -> Tuple:
        inmate = self._find_inmate(action.inmate_id)
        if inmate is None:
            return f"Inmate {action.inmate_id} not found.", False, -0.1, 0.0, False

        if inmate.assigned_program is None:
            return f"{action.inmate_id} is not yet assigned.", False, -0.05, 0.0, False

        new_program = action.program_type
        if new_program is None:
            return "program_type required for reschedule.", False, -0.1, 0.0, False

        if new_program == inmate.assigned_program:
            return f"{action.inmate_id} is already in {new_program.value}.", False, -0.05, 0.0, False

        if self._slots.get(new_program, 0) <= 0:
            return f"No slots in {new_program.value}.", False, -0.05, 0.0, False

        # Return old slot, restore risk partially
        old_program = inmate.assigned_program
        self._slots[old_program] += 1

        # Reset risk to before old assignment (approximate: re-add old reduction)
        old_reduction = compute_risk_reduction(
            InmateProfile(
                inmate.inmate_id, inmate.age, inmate.offence_category,
                inmate.initial_risk, inmate.receptivity,
                inmate.conflict_with, inmate.refused_programs,
            ),
            old_program,
        )
        inmate.risk_score = round(min(inmate.risk_score + old_reduction, inmate.initial_risk), 3)

        # Check conflicts for new program
        violation = self._check_conflict(inmate, new_program)
        if violation:
            # Restore old assignment
            inmate.assigned_program = old_program
            inmate.risk_score = round(max(0.0, inmate.risk_score - old_reduction), 3)
            self._slots[old_program] -= 1
            self._violations += 1
            return (
                f"Conflict: cannot move {action.inmate_id} to {new_program.value}.",
                False, -0.15, 0.0, False,
            )

        # Apply new assignment
        inmate.assigned_program = new_program
        self._slots[new_program] -= 1
        new_reduction = compute_risk_reduction(inmate, new_program)
        inmate.risk_score = round(max(0.0, inmate.risk_score - new_reduction), 3)

        net_gain = new_reduction - old_reduction
        step_reward = round(max(net_gain, 0) / 10.0, 4)

        return (
            f"Rescheduled {action.inmate_id}: {old_program.value} → {new_program.value}. "
            f"Net risk change: {net_gain:+.2f}.",
            True, 0.0, step_reward, False,
        )

    def _handle_dropout(self, action: RehabAction) -> Tuple:
        dropout = self._find_inmate(action.inmate_id)
        if dropout is None:
            return f"Inmate {action.inmate_id} not found.", False, -0.1, 0.0, False

        if dropout.assigned_program is None:
            return f"{action.inmate_id} is not assigned to any program.", False, -0.05, 0.0, False

        freed_program = dropout.assigned_program
        dropout.assigned_program = None
        dropout.dropout_count += 1
        self._slots[freed_program] += 1

        # Try to fill with replacement
        replacement = self._find_inmate(action.replacement_id) if action.replacement_id else None
        if replacement and replacement.assigned_program is None:
            if freed_program not in replacement.refused_programs:
                violation = self._check_conflict(replacement, freed_program)
                if not violation and self._slots.get(freed_program, 0) > 0:
                    replacement.assigned_program = freed_program
                    self._slots[freed_program] -= 1
                    reduction = compute_risk_reduction(replacement, freed_program)
                    replacement.risk_score = round(max(0.0, replacement.risk_score - reduction), 3)
                    return (
                        f"{action.inmate_id} dropped from {freed_program.value}. "
                        f"Replaced by {action.replacement_id} (risk -{reduction:.2f}).",
                        True, 0.0, round(reduction / 10.0, 4), False,
                    )

        self._wasted_slots += 1
        return (
            f"{action.inmate_id} dropped from {freed_program.value}. "
            f"Slot returned. No valid replacement found.",
            True, -0.05, 0.0, False,
        )

    def _handle_escalate(self, action: RehabAction) -> Tuple:
        inmate = self._find_inmate(action.inmate_id)
        if inmate is None:
            return f"Inmate {action.inmate_id} not found.", False, -0.1, 0.0, False

        if inmate.is_escalated:
            return f"{action.inmate_id} is already escalated.", False, -0.05, 0.0, False

        inmate.is_escalated = True
        # Escalation gives bonus risk reduction for high-risk inmates
        bonus = 0.3 if inmate.risk_score >= 7.0 else -0.1
        if bonus > 0:
            inmate.risk_score = round(max(0.0, inmate.risk_score - bonus), 3)

        return (
            f"Escalated {action.inmate_id} (risk={inmate.risk_score:.2f}). "
            f"{'Counsellor assigned.' if bonus > 0 else 'Low-risk escalation — minor penalty.'}",
            True, max(-bonus, 0.0), max(bonus / 10.0, 0.0), False,
        )

    def _handle_reallocate(self, action: RehabAction) -> Tuple:
        if action.from_program is None or action.to_program is None or action.slots is None:
            return "from_program, to_program, and slots required.", False, -0.1, 0.0, False

        transfer = max(1, min(action.slots, self._slots.get(action.from_program, 0)))
        self._slots[action.from_program] = max(0, self._slots[action.from_program] - transfer)
        self._slots[action.to_program]   = self._slots.get(action.to_program, 0) + transfer
        self._capacity[action.to_program] = self._slots[action.to_program]

        self._state.budget_cuts_applied += 1

        return (
            f"Reallocated {transfer} slots from {action.from_program.value} "
            f"to {action.to_program.value}.",
            True, 0.0, 0.0, False,
        )

    def _handle_submit(self, action: RehabAction) -> Tuple:
        final_reward = self._compute_final_reward()
        self._state.grader_score = final_reward
        return (
            f"Schedule submitted. Final grader score: {final_reward:.4f}",
            True, 0.0, final_reward, True,
        )

    # ──────────────────────────────
    # Helpers
    # ──────────────────────────────

    def _find_inmate(self, inmate_id: Optional[str]) -> Optional[InmateProfile]:
        if inmate_id is None:
            return None
        for inmate in self._inmates:
            if inmate.inmate_id == inmate_id:
                return inmate
        return None

    def _check_conflict(self, inmate: InmateProfile, program: ProgramType) -> Optional[str]:
        """Return conflicting inmate_id if one exists in the same program, else None."""
        for other in self._inmates:
            if (
                other.inmate_id != inmate.inmate_id
                and other.assigned_program == program
                and other.inmate_id in inmate.conflict_with
            ):
                return other.inmate_id
        return None

    def _avg_risk(self) -> float:
        if not self._inmates:
            return 0.0
        return sum(i.risk_score for i in self._inmates) / len(self._inmates)

    def _maybe_add_arrivals(self):
        """Task 3: add 4 new inmates every 5 steps."""
        if self._dynamic_pool and self._state.step_count % 5 == 0:
            arrivals = self._dynamic_pool[:4]
            self._dynamic_pool = self._dynamic_pool[4:]
            self._inmates.extend(arrivals)
            self._state.total_inmates = len(self._inmates)

    def _maybe_apply_budget_cut(self):
        """Task 3: remove vocational training at step 10."""
        if not self._budget_cut and self._state.step_count == 10:
            self._budget_cut = True
            self._state.budget_cuts_applied += 1
            # Unassign all vocational inmates — they need to be rescheduled
            for inmate in self._inmates:
                if inmate.assigned_program == ProgramType.VOCATIONAL:
                    inmate.assigned_program = None
                    inmate.risk_score = round(
                        min(inmate.risk_score + 1.5, inmate.initial_risk), 3
                    )
            self._slots[ProgramType.VOCATIONAL]   = 0
            self._capacity[ProgramType.VOCATIONAL] = 0

    def _compute_final_reward(self) -> float:
        return _grade(
            inmates=self._inmates,
            violations=self._violations,
            wasted_slots=self._wasted_slots,
            total_slots=sum(self._capacity.values()),
            steps_taken=self._state.step_count,
            max_steps=self.MAX_STEPS[self._task_id],
            optimal_score=self._optimal_score,
        )

    def _make_observation(
        self,
        last_result: str,
        last_valid: bool,
        last_penalty: float,
        reward: Optional[float],
        done: bool,
    ) -> RehabObservation:
        assigned  = sum(1 for i in self._inmates if i.assigned_program)
        waitlist  = [i.inmate_id for i in self._inmates if i.assigned_program is None]
        reduction = (
            (self._state.initial_avg_risk - self._avg_risk()) /
            max(self._state.initial_avg_risk, 1e-6)
        )
        return RehabObservation(
            done=done,
            reward=reward,
            inmates=[i.to_dict() for i in self._inmates],
            total_inmates=len(self._inmates),
            assigned_count=assigned,
            unassigned_count=len(self._inmates) - assigned,
            escalated_count=sum(1 for i in self._inmates if i.is_escalated),
            program_slots={p.value: s for p, s in self._slots.items()},
            program_capacity={p.value: c for p, c in self._capacity.items()},
            waitlist=waitlist[:20],  # top 20 unassigned
            avg_risk_score=round(self._avg_risk(), 3),
            risk_reduction_so_far=round(max(reduction, 0.0), 4),
            constraint_violations=self._violations,
            wasted_slots=self._wasted_slots,
            last_action_result=last_result,
            last_action_valid=last_valid,
            last_action_penalty=last_penalty,
            task_id=self._task_id,
            budget_remaining={p.value: s for p, s in self._slots.items()},
            steps_remaining=self.MAX_STEPS[self._task_id] - self._state.step_count,
        )

    # ──────────────────────────────
    # state property
    # ──────────────────────────────

    @property
    def state(self) -> RehabState:
        return self._state
