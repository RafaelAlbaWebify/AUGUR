from __future__ import annotations

import re

from app.esco_store import esco_status, occupation_skill_rows


def _normalize(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9+#.]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def _matches(user_skill: str, labels: list[str]) -> bool:
    normalized_user = _normalize(user_skill)
    if not normalized_user:
        return False

    for label in labels:
        normalized_label = _normalize(label)
        if not normalized_label:
            continue

        if normalized_user == normalized_label:
            return True

        if normalized_user in normalized_label:
            return True

        if normalized_label in normalized_user:
            return True

    return False


def match_profile_skills(
    occupation_label: str,
    profile_skills: list[str],
) -> dict:
    status = esco_status()
    rows = occupation_skill_rows(occupation_label)

    if not rows:
        return {
            "status": "occupation_not_loaded",
            "dataset_mode": status["mode"],
            "dataset_version": status["version"],
            "occupation_label": occupation_label,
            "matched_skills": [],
            "missing_skills": [],
            "coverage": None,
            "evidence_complete": False,
        }

    matched = []
    missing = []

    for row in rows:
        labels = [
            row["skill_label"],
            *row["alternative_labels"],
        ]
        profile_matches = [
            skill
            for skill in profile_skills
            if _matches(skill, labels)
        ]

        item = {
            "skill_uri": row["skill_uri"],
            "skill_label": row["skill_label"],
            "relation_type": row["relation_type"],
            "profile_matches": profile_matches,
        }

        if profile_matches:
            matched.append(item)
        elif row["relation_type"] == "essential":
            missing.append(item)

    essential_total = sum(
        1
        for row in rows
        if row["relation_type"] == "essential"
    )
    essential_matched = sum(
        1
        for row in matched
        if row["relation_type"] == "essential"
    )

    coverage = (
        essential_matched / essential_total
        if essential_total
        else None
    )

    # Seed mode is intentionally partial and can never be "complete".
    evidence_complete = (
        status["mode"] == "full"
        and essential_total > 0
    )

    return {
        "status": (
            "matched"
            if matched
            else "no_profile_skill_match"
        ),
        "dataset_mode": status["mode"],
        "dataset_version": status["version"],
        "occupation_label": occupation_label,
        "matched_skills": matched,
        "missing_skills": missing,
        "essential_skill_count": essential_total,
        "essential_skills_matched": essential_matched,
        "coverage": coverage,
        "evidence_complete": evidence_complete,
    }
