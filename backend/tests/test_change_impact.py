"""Change impact harness contracts: pure, no repo mutations or network needed."""
from scripts.change_impact import analyze, typescript_edges, unresolved_typescript_imports, missing_frontend_api_routes


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


def test_typescript_relative_imports_resolve_reverse_consumers(tmp_path):
    root=tmp_path
    source=root / "frontend" / "src"
    (source / "components").mkdir(parents=True)
    (source / "components" / "ComparePanel.tsx").write_text("export default 1", encoding="utf-8")
    (source / "App.tsx").write_text(
        'import ComparePanel from "./components/ComparePanel"\\n', encoding="utf-8"
    )
    edges=typescript_edges(root)
    assert edges["frontend/src/components/ComparePanel.tsx"] == ["frontend/src/App.tsx"]
    result=analyze(["frontend/src/components/ComparePanel.tsx"],
                   {"files":[]},edges)
    assert "frontend/src/App.tsx" in result["items"][0]["importers"]


def test_dynamic_typescript_import_is_not_assumed_to_be_resolved(tmp_path):
    source=tmp_path / "frontend" / "src"
    source.mkdir(parents=True)
    (source / "source.ts").write_text("export const x = 1", encoding="utf-8")
    (source / "load.ts").write_text("import(pathFromUser)", encoding="utf-8")
    assert typescript_edges(tmp_path) == {}


def test_missing_frontend_import_is_detected_before_integration(tmp_path):
    src = tmp_path / "frontend" / "src"
    src.mkdir(parents=True)
    (src / "App.tsx").write_text('import Widget from "./MissingWidget"\\n', encoding="utf-8")
    assert unresolved_typescript_imports(tmp_path) == [
        {"importer": "frontend/src/App.tsx", "specifier": "./MissingWidget"}
    ]
    (src / "MissingWidget.tsx").write_text("export default function Widget() {}", encoding="utf-8")
    assert unresolved_typescript_imports(tmp_path) == []

def test_api_route_gate_detects_deleted_endpoint_and_recovers(tmp_path):
    backend = tmp_path / 'backend' / 'app' / 'api'
    frontend = tmp_path / 'frontend' / 'src'
    backend.mkdir(parents=True)
    frontend.mkdir(parents=True)
    (frontend / 'App.tsx').write_text(
        'const request = `${API_BASE}/api/compare?countries=${query}`',
        encoding='utf-8',
    )
    main = backend.parent / 'main.py'
    main.write_text('app.include_router(router, prefix="/api")\n', encoding='utf-8')
    routes = backend / 'routes.py'
    routes.write_text('@router.get("/health")\ndef health(): pass\n', encoding='utf-8')
    assert missing_frontend_api_routes(tmp_path) == ['/api/compare']
    routes.write_text('@router.get("/compare")\ndef compare(): pass\n', encoding='utf-8')
    assert missing_frontend_api_routes(tmp_path) == []

def test_router_prefix_configuration_drift_fails_contract(tmp_path):
    backend = tmp_path / "backend" / "app" / "api"
    frontend = tmp_path / "frontend" / "src"
    backend.mkdir(parents=True)
    frontend.mkdir(parents=True)
    main = backend.parent / "main.py"
    main.write_text('app.include_router(router, prefix="/api")\n', encoding="utf-8")
    (backend / "routes.py").write_text('@router.get("/compare")\ndef compare(): pass\n', encoding="utf-8")
    (frontend / "App.tsx").write_text('fetch(`${API_BASE}/api/compare`)', encoding="utf-8")
    assert missing_frontend_api_routes(tmp_path) == []
    main.write_text('app.include_router(router, prefix="/api/v2")\n', encoding="utf-8")
    assert missing_frontend_api_routes(tmp_path) == ["/api/compare"]
    main.write_text('app.include_router(router, prefix="/api")\n', encoding="utf-8")
    assert missing_frontend_api_routes(tmp_path) == []


def test_missing_contract_input_fails_closed(tmp_path):
    assert any("Required API contract input missing" in issue
               for issue in missing_frontend_api_routes(tmp_path))


def test_missing_country_route_map_fails_closed(tmp_path):
    backend=tmp_path / "backend" / "app" / "api"
    frontend=tmp_path / "frontend" / "src"
    backend.mkdir(parents=True)
    frontend.mkdir(parents=True)
    (backend.parent / "main.py").write_text('app.include_router(router, prefix="/api")', encoding="utf-8")
    (backend / "routes.py").write_text('@router.get("/countries/{country_iso3}/snapshot")', encoding="utf-8")
    (frontend / "App.tsx").write_text(
        'fetch(`${API_BASE}/api/countries/${selectedCountry}/${paths[key]}`)', encoding="utf-8"
    )
    assert missing_frontend_api_routes(tmp_path) == ["Cannot resolve frontend country API path map"]
