"""
Rehabilitation Scheduler — Case Generator
Procedurally generates inmate populations and program configurations
for all 3 task difficulty levels. Seeded for reproducibility.
"""

import random
from typing import List, Dict, Tuple
from models import InmateProfile, ProgramType


# ─────────────────────────────────────────────
# Program effectiveness table
# How much each program reduces risk_score
# per unit of inmate receptivity
# ─────────────────────────────────────────────

PROGRAM_EFFECTIVENESS: Dict[ProgramType, float] = {
    ProgramType.EDUCATION:       1.8,
    ProgramType.THERAPY:         2.2,
    ProgramType.VOCATIONAL:      1.5,
    ProgramType.SUBSTANCE_ABUSE: 2.5,
    ProgramType.ANGER_MGMT:      2.0,
}

# Which offence categories respond best to which programs
OFFENCE_PROGRAM_AFFINITY: Dict[str, List[ProgramType]] = {
    "drug":     [ProgramType.SUBSTANCE_ABUSE, ProgramType.THERAPY],
    "violent":  [ProgramType.ANGER_MGMT, ProgramType.THERAPY],
    "property": [ProgramType.VOCATIONAL, ProgramType.EDUCATION],
    "fraud":    [ProgramType.EDUCATION, ProgramType.VOCATIONAL],
    "dui":      [ProgramType.SUBSTANCE_ABUSE, ProgramType.ANGER_MGMT],
}

OFFENCE_CATEGORIES = list(OFFENCE_PROGRAM_AFFINITY.keys())


def _make_inmate(
    idx: int,
    rng: random.Random,
    force_high_risk: bool = False,
    force_conflict_with: Optional[List[str]] = None,
) -> InmateProfile:
    """Generate one inmate with realistic attributes."""
    from typing import Optional  # local import to avoid circular at module level

    inmate_id = f"I-{idx:03d}"
    age = rng.randint(18, 55)
    offence = rng.choice(OFFENCE_CATEGORIES)

    if force_high_risk:
        risk_score = round(rng.uniform(7.0, 10.0), 2)
    else:
        risk_score = round(rng.uniform(1.0, 10.0), 2)

    receptivity = round(rng.uniform(0.3, 1.0), 2)

    # ~20% of inmates refuse at least one program
    refused = []
    if rng.random() < 0.2:
        refused = rng.sample(list(ProgramType), k=rng.randint(1, 2))

    return InmateProfile(
        inmate_id=inmate_id,
        age=age,
        offence_category=offence,
        risk_score=risk_score,
        receptivity=receptivity,
        conflict_with=force_conflict_with or [],
        refused_programs=refused,
    )


def compute_risk_reduction(inmate: InmateProfile, program: ProgramType) -> float:
    """
    How much risk_score decreases when this inmate attends this program.
    Formula: effectiveness × receptivity × affinity_bonus
    Capped so risk_score never goes below 0.
    """
    base = PROGRAM_EFFECTIVENESS[program]
    affinity_bonus = (
        1.3 if program in OFFENCE_PROGRAM_AFFINITY.get(inmate.offence_category, [])
        else 1.0
    )
    reduction = base * inmate.receptivity * affinity_bonus
    return round(min(reduction, inmate.risk_score), 3)


# ─────────────────────────────────────────────
# Task configurations
# ─────────────────────────────────────────────

def generate_task_1(seed: int = 42) -> Tuple[List[InmateProfile], Dict[ProgramType, int]]:
    """
    EASY — 20 inmates, 25 slots across 5 program types.
    No conflicts. No refusals. Sufficient capacity for everyone.
    Clear risk ordering. Agent should achieve near-perfect allocation.
    """
    rng = random.Random(seed)
    inmates = [_make_inmate(i, rng) for i in range(1, 21)]

    # Generous slots — enough for all 20 inmates plus 5 buffer
    slots = {
        ProgramType.EDUCATION:       5,
        ProgramType.THERAPY:         6,
        ProgramType.VOCATIONAL:      5,
        ProgramType.SUBSTANCE_ABUSE: 5,
        ProgramType.ANGER_MGMT:      4,
    }
    return inmates, slots


def generate_task_2(seed: int = 42) -> Tuple[List[InmateProfile], Dict[ProgramType, int]]:
    """
    MEDIUM — 50 inmates, 60% capacity (30 total slots).
    3 inmates refuse specific programs.
    5 conflict pairs — cannot share any session.
    2 high-risk arrivals mid-episode (dynamic).
    Agent must prioritize high-risk inmates and respect constraints.
    """
    rng = random.Random(seed)
    inmates = [_make_inmate(i, rng) for i in range(1, 51)]

    # Force 5 specific high-risk inmates for realism
    for i in [3, 7, 15, 22, 38]:
        inmates[i - 1].risk_score = round(rng.uniform(7.5, 10.0), 2)
        inmates[i - 1].initial_risk = inmates[i - 1].risk_score

    # Conflict pairs (by index, 0-based)
    conflict_pairs = [(2, 9), (14, 21), (30, 37), (4, 44), (11, 25)]
    for a, b in conflict_pairs:
        inmates[a].conflict_with.append(inmates[b].inmate_id)
        inmates[b].conflict_with.append(inmates[a].inmate_id)

    # Force 3 refusals
    inmates[5].refused_programs  = [ProgramType.THERAPY]
    inmates[18].refused_programs = [ProgramType.EDUCATION, ProgramType.VOCATIONAL]
    inmates[33].refused_programs = [ProgramType.SUBSTANCE_ABUSE]

    # 30 slots (60% of 50 inmates)
    slots = {
        ProgramType.EDUCATION:       6,
        ProgramType.THERAPY:         7,
        ProgramType.VOCATIONAL:      6,
        ProgramType.SUBSTANCE_ABUSE: 6,
        ProgramType.ANGER_MGMT:      5,
    }
    return inmates, slots


def generate_task_3(seed: int = 42) -> Tuple[List[InmateProfile], Dict[ProgramType, int]]:
    """
    HARD — 200 inmates, dynamic arrivals every 5 steps.
    Budget cut mid-episode: vocational training removed at step 10.
    Multiple conflict clusters. High refusal rate.
    Agent must re-optimize live without restarting.
    """
    rng = random.Random(seed)

    # 180 initial + 20 arrive dynamically
    inmates = [_make_inmate(i, rng) for i in range(1, 181)]

    # 30% are high-risk
    high_risk_indices = rng.sample(range(180), k=54)
    for idx in high_risk_indices:
        inmates[idx].risk_score = round(rng.uniform(7.0, 10.0), 2)
        inmates[idx].initial_risk = inmates[idx].risk_score

    # Conflict clusters (groups of 3 who all conflict with each other)
    clusters = [
        [10, 25, 40],
        [60, 75, 90],
        [120, 135, 150],
        [5, 20, 35],
        [100, 115, 130],
    ]
    for cluster in clusters:
        for a in cluster:
            for b in cluster:
                if a != b:
                    inmates[a].conflict_with.append(inmates[b].inmate_id)

    # Higher refusal rate (30%)
    refusal_indices = rng.sample(range(180), k=54)
    for idx in refusal_indices:
        refused_count = rng.randint(1, 2)
        inmates[idx].refused_programs = rng.sample(list(ProgramType), k=refused_count)

    # Initial slots (will be modified mid-episode by budget cut)
    slots = {
        ProgramType.EDUCATION:       30,
        ProgramType.THERAPY:         35,
        ProgramType.VOCATIONAL:      25,   # <- removed at step 10
        ProgramType.SUBSTANCE_ABUSE: 28,
        ProgramType.ANGER_MGMT:      22,
    }

    # Dynamic arrivals (20 inmates who join mid-episode)
    dynamic_arrivals = [
        _make_inmate(180 + i, rng, force_high_risk=(i % 3 == 0))
        for i in range(1, 21)
    ]

    return inmates + dynamic_arrivals, slots


# ─────────────────────────────────────────────
# Optimal score calculator (for grader baseline)
# ─────────────────────────────────────────────

def compute_optimal_score(
    inmates: List[InmateProfile],
    slots: Dict[ProgramType, int],
) -> float:
    """
    Greedy oracle: assigns each inmate their best program (highest reduction)
    respecting slot capacity. Returns total risk reduction / initial total risk.
    Used to normalize grader scores to 0.0–1.0.
    """
    slot_remaining = dict(slots)
    total_initial_risk = sum(i.risk_score for i in inmates)
    if total_initial_risk == 0:
        return 1.0

    # Sort by risk score descending — prioritize high-risk
    sorted_inmates = sorted(inmates, key=lambda x: -x.risk_score)

    total_reduction = 0.0
    for inmate in sorted_inmates:
        best_reduction = 0.0
        best_program = None
        for program in ProgramType:
            if program in inmate.refused_programs:
                continue
            if slot_remaining.get(program, 0) <= 0:
                continue
            reduction = compute_risk_reduction(inmate, program)
            if reduction > best_reduction:
                best_reduction = reduction
                best_program = program
        if best_program:
            slot_remaining[best_program] -= 1
            total_reduction += best_reduction

    return round(min(total_reduction / total_initial_risk, 1.0), 4)


# Make Optional importable at module level for _make_inmate
from typing import Optional  # noqa: E402
