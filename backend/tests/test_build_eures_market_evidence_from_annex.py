from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

from scripts import build_eures_market_evidence_from_annex as module


def _configure_paths(monkeypatch, tmp_path):
    project_root = tmp_path
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    monkeypatch.setattr(
        module,
        "settings",
        SimpleNamespace(
            project_root=project_root,
            data_dir=data_dir,
        ),
    )
    manifest = (
        project_root
        / "backend"
        / "app"
        / "evidence"
        / "eures_lmi_2025.json"
    )
    manifest.parent.mkdir(parents=True)
    manifest.write_text(
        json.dumps({
            "unit_group_signals": {
                "2511": {
                    "occupation_label": "Systems analysts",
                    "shortage_countries": ["IE"],
                    "surplus_countries": [],
                }
            }
        }),
        encoding="utf-8",
    )
    return manifest


def test_annex_pipeline_writes_candidate_only_after_resolved_review(
    monkeypatch,
    tmp_path,
):
    _configure_paths(monkeypatch, tmp_path)
    pdf = tmp_path / "annex.pdf"
    pdf.write_bytes(b"%PDF-test")
    normalized = tmp_path / "normalized.csv"
    review_output = tmp_path / "review.json"
    candidate_output = tmp_path / "candidate.json"

    monkeypatch.setattr(module, "initialize_datastores", lambda: None)
    monkeypatch.setattr(
        module,
        "extract_eures_annex_rows_from_pdf",
        lambda path: (
            [{
                "occupation_label": "Systems analysts",
                "shortage_countries": "IE",
                "surplus_countries": "",
            }],
            {
                "row_count": 1,
                "table_count": 1,
                "pages_with_rows": 1,
                "duplicate_conflict_count": 0,
                "ready_for_esco_review": True,
            },
        ),
    )
    monkeypatch.setattr(
        module,
        "write_normalized_annex_csv",
        lambda rows, path: Path(path),
    )
    review = {
        "ready_for_review": True,
        "resolved_count": 1,
        "unresolved_count": 0,
        "esco_version": "1.2.1",
        "unresolved": [],
    }
    monkeypatch.setattr(
        module,
        "build_eures_unit_group_evidence_from_csv",
        lambda *args, **kwargs: review,
    )

    def fake_write_review(result, path):
        output = Path(path)
        output.write_text(json.dumps(result), encoding="utf-8")
        return output

    monkeypatch.setattr(
        module,
        "write_eures_review_artifact",
        fake_write_review,
    )
    monkeypatch.setattr(
        module,
        "build_eures_manifest_candidate_from_files",
        lambda review_path, manifest_path: {
            "candidate_manifest": {
                "unit_group_signals": {
                    "2511": {
                        "occupation_label": "Systems analysts",
                        "shortage_countries": ["IE"],
                        "surplus_countries": [],
                    }
                }
            },
            "comparison": {
                "current_unit_group_count": 1,
                "candidate_unit_group_count": 1,
                "added_unit_groups": [],
                "removed_unit_groups": [],
                "changed_existing_unit_groups": [],
                "unchanged_existing_count": 1,
            },
        },
    )

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "build_eures_market_evidence_from_annex",
            "--pdf",
            str(pdf),
            "--normalized-output",
            str(normalized),
            "--review-output",
            str(review_output),
            "--candidate-output",
            str(candidate_output),
        ],
    )

    code = module.main()

    assert code == 0
    assert candidate_output.exists()
    payload = json.loads(candidate_output.read_text(encoding="utf-8"))
    assert "2511" in payload["unit_group_signals"]


def test_annex_pipeline_returns_partial_when_candidate_guard_rejects_review(
    monkeypatch,
    tmp_path,
    capsys,
):
    _configure_paths(monkeypatch, tmp_path)
    pdf = tmp_path / "annex.pdf"
    pdf.write_bytes(b"%PDF-test")
    review_output = tmp_path / "review.json"
    candidate_output = tmp_path / "candidate.json"

    monkeypatch.setattr(module, "initialize_datastores", lambda: None)
    monkeypatch.setattr(
        module,
        "extract_eures_annex_rows_from_pdf",
        lambda path: (
            [{
                "occupation_label": "Systems analysts",
                "shortage_countries": "IE",
                "surplus_countries": "",
            }],
            {
                "row_count": 1,
                "table_count": 1,
                "pages_with_rows": 1,
                "duplicate_conflict_count": 0,
                "ready_for_esco_review": True,
            },
        ),
    )
    monkeypatch.setattr(
        module,
        "write_normalized_annex_csv",
        lambda rows, path: Path(path),
    )
    review = {
        "ready_for_review": True,
        "resolved_count": 1,
        "unresolved_count": 0,
        "esco_version": "1.2.1",
        "unresolved": [],
    }
    monkeypatch.setattr(
        module,
        "build_eures_unit_group_evidence_from_csv",
        lambda *args, **kwargs: review,
    )

    def fake_write_review(result, path):
        output = Path(path)
        output.write_text(json.dumps(result), encoding="utf-8")
        return output

    monkeypatch.setattr(
        module,
        "write_eures_review_artifact",
        fake_write_review,
    )
    monkeypatch.setattr(
        module,
        "build_eures_manifest_candidate_from_files",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            ValueError("candidate review has fewer unit groups than current production evidence")
        ),
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "build_eures_market_evidence_from_annex",
            "--pdf",
            str(pdf),
            "--review-output",
            str(review_output),
            "--candidate-output",
            str(candidate_output),
        ],
    )

    code = module.main()
    output = capsys.readouterr().out

    assert code == 2
    assert "status: partial" in output
    assert "fewer unit groups" in output
    assert not candidate_output.exists()
