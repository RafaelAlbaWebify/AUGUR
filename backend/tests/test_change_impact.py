"""Change impact harness contracts: pure, no repo mutations or network needed."""
from scripts.change_impact import analyze


def test_python_import_graph_exposes_callers_and_tests():
    inventory={"files":[
        {"path":"backend/app/db/write_contract.py",
         "imported_by":["backend/app/db/analytics.py","backend/tests/test_observation_write_contract.py"],
         "resolved_local_imports":[],"review_status":"verified_reviewed"}
    ]}
    result=analyze(["backend/app/db/write_contract.py"],inventory)
    item=result["items"][0]
    assert item["importers"] == [
        "backend/app/db/analytics.py","backend/tests/test_observation_write_contract.py"
    ]
    assert "backend/tests/test_observation_write_contract.py" in item["test_hints"]
    assert "backend/app/db/analytics.py" in item["contract_hints"]
    assert result["complete_graph"] is False


def test_unknown_new_file_is_flagged_not_misreported_as_covered():
    item=analyze(["frontend/src/new-component.tsx"],{"files":[]})["items"][0]
    assert any("absent" in reason for reason in item["uncovered_risks"])
    assert any("not indexed" in reason for reason in item["uncovered_risks"])


def test_duplicate_paths_do_not_inflate_impact():
    result=analyze(["docs/a.md","docs/a.md"],{"files":[]})
    assert result["changed_files"] == 1


def test_stale_review_requires_explicit_warning():
    inventory={"files":[{"path":"backend/app/example.py",
                         "imported_by":[],"resolved_local_imports":[],
                         "review_status":"stale_review"}]}
    item=analyze(["backend/app/example.py"],inventory)["items"][0]
    assert any("invalidated" in reason for reason in item["uncovered_risks"])
