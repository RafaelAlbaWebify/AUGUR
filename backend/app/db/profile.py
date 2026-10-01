from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

from app.core.config import settings
from app.models.profile import PersonalProfile, PersonalProfileResponse


PROFILE_ID = "default"


def _loads(value: str | None, fallback):
    if not value:
        return fallback
    return json.loads(value)


def get_profile() -> PersonalProfileResponse:
    con = sqlite3.connect(settings.sqlite_path)
    con.row_factory = sqlite3.Row

    try:
        row = con.execute(
            "SELECT * FROM personal_profile WHERE profile_id = ?",
            [PROFILE_ID],
        ).fetchone()
    finally:
        con.close()

    if row is None:
        return PersonalProfileResponse(
            profile_id=PROFILE_ID,
            updated_at=None,
        )

    return PersonalProfileResponse(
        profile_id=row["profile_id"],
        age=row["age"],
        current_country=row["current_country"],
        citizenships=_loads(row["citizenships_json"], []),
        profession=row["profession"],
        skills=_loads(row["skills_json"], []),
        languages=_loads(row["languages_json"], []),
        household_size=row["household_size"],
        monthly_net_income=row["monthly_net_income"],
        liquid_savings=row["liquid_savings"],
        remote_work=bool(row["remote_work"]),
        preferences=_loads(row["preferences_json"], {}),
        updated_at=row["updated_at"],
    )


def save_profile(profile: PersonalProfile) -> PersonalProfileResponse:
    updated_at = datetime.now(timezone.utc).isoformat()

    con = sqlite3.connect(settings.sqlite_path)
    try:
        con.execute(
            """
            INSERT OR REPLACE INTO personal_profile (
                profile_id,
                age,
                current_country,
                citizenships_json,
                profession,
                skills_json,
                languages_json,
                household_size,
                monthly_net_income,
                liquid_savings,
                remote_work,
                preferences_json,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                PROFILE_ID,
                profile.age,
                profile.current_country.upper() if profile.current_country else None,
                json.dumps([value.upper() for value in profile.citizenships]),
                profile.profession,
                json.dumps(profile.skills),
                json.dumps([item.model_dump() for item in profile.languages]),
                profile.household_size,
                profile.monthly_net_income,
                profile.liquid_savings,
                1 if profile.remote_work else 0,
                json.dumps(profile.preferences),
                updated_at,
            ],
        )
        con.commit()
    finally:
        con.close()

    return get_profile()
