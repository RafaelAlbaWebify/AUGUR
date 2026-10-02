from pathlib import Path
from types import SimpleNamespace

from app.db.bootstrap import initialize_sqlite
from app import esco_store
from app.services import esco_match


def _point_modules_to_tmp_db(monkeypatch, tmp_path: Path):
    fake_settings = SimpleNamespace(sqlite_path=tmp_path / "esco.sqlite")
    monkeypatch.setattr(esco_store, "settings", fake_settings)
    monkeypatch.setattr(esco_match, "esco_status", esco_store.esco_status)
    monkeypatch.setattr(esco_match, "occupation_skill_rows", esco_store.occupation_skill_rows)
    initialize_sqlite(fake_settings.sqlite_path)
    return fake_settings.sqlite_path


def test_partial_seed_never_marks_skill_evidence_complete(monkeypatch, tmp_path):
    _point_modules_to_tmp_db(monkeypatch, tmp_path)

    status = esco_store.seed_esco_partial()
    assert status["mode"] == "seed"
    assert status["occupation_count"] >= 2
    assert status["skill_count"] >= 3

    result = esco_match.match_profile_skills(
        "ICT system administrator",
        ["VPN", "ICT system upgrade"],
    )

    assert result["dataset_mode"] == "seed"
    assert result["essential_skills_matched"] == 2
    assert result["coverage"] == 1.0
    assert result["evidence_complete"] is False


def test_official_csv_package_can_be_imported_as_full(monkeypatch, tmp_path):
    _point_modules_to_tmp_db(monkeypatch, tmp_path)

    package = tmp_path / "package"
    package.mkdir()

    (package / "occupations_en.csv").write_text(
        "conceptUri,preferredLabel,code,iscoGroup\n"
        "urn:test:occupation,ICT system administrator,2522.1,2522\n",
        encoding="utf-8",
    )
    (package / "skills_en.csv").write_text(
        "conceptUri,preferredLabel,altLabels\n"
        "urn:test:skill,manage changes in ICT system,ICT system upgrade\n",
        encoding="utf-8",
    )
    (package / "occupationSkillRelations_en.csv").write_text(
        "occupationUri,skillUri,relationType\n"
        "urn:test:occupation,urn:test:skill,essential\n",
        encoding="utf-8",
    )

    status = esco_store.import_esco_csv_package(package, version="test-version")

    assert status["mode"] == "full"
    assert status["version"] == "test-version"
    assert status["occupation_count"] == 1
    assert status["skill_count"] == 1
    assert status["relation_count"] == 1

    result = esco_match.match_profile_skills(
        "ICT system administrator",
        ["ICT system upgrade"],
    )

    assert result["dataset_mode"] == "full"
    assert result["coverage"] == 1.0
    assert result["evidence_complete"] is True


def test_search_occupations_normalizes_it_to_ict(monkeypatch, tmp_path):
    _point_modules_to_tmp_db(monkeypatch, tmp_path)
    esco_store.seed_esco_partial()

    results = esco_store.search_occupations("IT system administrator")

    assert results
    assert results[0]["preferred_label"] == "ICT system administrator"
    assert results[0]["match_score"] >= 0.9
    assert results[0]["match_method"] in {"exact_label", "label_contains"}


def test_search_occupations_orders_best_match_first(monkeypatch, tmp_path):
    _point_modules_to_tmp_db(monkeypatch, tmp_path)
    esco_store.seed_esco_partial()

    results = esco_store.search_occupations("network engineer")

    assert results
    assert results[0]["preferred_label"] == "ICT network engineer"
    assert results[0]["match_score"] >= results[-1]["match_score"]
