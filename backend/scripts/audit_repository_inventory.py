"""Static AUGUR repository code inventory; AST-only, no imports or application execution.

Usage: python backend/scripts/audit_repository_inventory.py
       python backend/scripts/audit_repository_inventory.py --check
Inventory counts are not a substitute for line-by-line review.
"""
from __future__ import annotations
import argparse
import ast
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "docs" / "audit" / "inventory.json"
EXTENSIONS = {".py", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".ps1", ".yml", ".yaml"}
EXCLUDE_DIRS = {".git", "node_modules", ".venv", "venv", "dist", "build", "__pycache__", ".pytest_cache", "playwright-report", "test-results"}
TOP = ("backend/app/", "backend/scripts/", "backend/tests/", "frontend/", ".github/workflows/", "tools/")

def bucket(path: str) -> str:
    if path.startswith("backend/app/"):
        rest = path[len("backend/app/"):]
        return "backend/app/" + (rest.split("/")[0] if "/" in rest else "_root")
    for prefix, label in [("backend/scripts/", "backend/scripts"), ("backend/tests/", "backend/tests"),
                          ("frontend/", "frontend"), (".github/workflows/", "github/workflows"),
                          ("tools/", "tools")]:
        if path.startswith(prefix):
            return label
    return "other"

def analyze_py(path: Path, rel: str) -> dict:
    data = path.read_text(encoding="utf-8-sig")
    tree = ast.parse(data, filename=rel)
    definitions = []
    imports = []
    calls = []
    class Visitor(ast.NodeVisitor):
        def __init__(self): self.scope = []
        def visit_ClassDef(self, node):
            self.record(node, "class")
            self.scope.append(node.name); self.generic_visit(node); self.scope.pop()
        def visit_FunctionDef(self, node):
            self.record(node, "function")
            self.scope.append(node.name); self.generic_visit(node); self.scope.pop()
        def visit_AsyncFunctionDef(self, node):
            self.record(node, "async_function")
            self.scope.append(node.name); self.generic_visit(node); self.scope.pop()
        def record(self, node, kind):
            definitions.append({"symbol": ".".join(self.scope + [node.name]), "kind": kind,
                "line_start": node.lineno, "line_end": node.end_lineno,
                "signature_arguments": [arg.arg for arg in node.args.args] if hasattr(node, "args") else []})
        def visit_Import(self, node):
            imports.extend({"module": n.name, "line": node.lineno} for n in node.names)
        def visit_ImportFrom(self, node):
            imports.append({"module": ("." * node.level) + (node.module or ""), "line": node.lineno})
        def visit_Call(self, node):
            target = node.func
            if isinstance(target, ast.Name): name = target.id
            elif isinstance(target, ast.Attribute): name = target.attr
            else: name = None
            if name: calls.append(name)
            self.generic_visit(node)
    Visitor().visit(tree)
    return {"definitions": definitions, "imports": imports,
            "called_names": sorted(set(calls)), "lines": len(data.splitlines())}

def generate() -> dict:
    paths = sorted((p for p in ROOT.rglob("*") if p.is_file()
                    and not EXCLUDE_DIRS.intersection(p.relative_to(ROOT).parts)
                    and (str(p.relative_to(ROOT)).startswith(TOP))
                    and (p.suffix.lower() in EXTENSIONS)), key=lambda p: p.as_posix())
    modules, errors = [], []
    for path in paths:
        rel = path.relative_to(ROOT).as_posix()
        info = {"path": rel, "bucket": bucket(rel),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "bytes": path.stat().st_size,
                "review_status": "not_reviewed"}
        if path.suffix == ".py":
            try: info.update(analyze_py(path, rel))
            except (SyntaxError, UnicodeError) as exc:
                errors.append({"path": rel, "error": str(exc)})
        modules.append(info)
    if errors: raise RuntimeError("Cannot certify inventory of unparsable source files: " + json.dumps(errors))
    by_path = {item["path"]: item for item in modules}
    imported_by: dict[str, set[str]] = {path: set() for path in by_path}
    reviewed = {}
    findings_path = ROOT / "docs" / "audit" / "findings.json"
    if findings_path.exists():
        findings = json.loads(findings_path.read_text(encoding="utf-8"))
        reviewed = {entry["path"]: entry["sha256"] for entry in findings.get("reviewed_files", [])}
    for item in modules:
        path = item["path"]
        original = reviewed.get(path)
        item["review_status"] = (
            "verified_reviewed" if original == item["sha256"] else
            "stale_review" if original is not None else "not_reviewed"
        )
        if not path.endswith(".py"):
            continue
        targets = set()
        for declaration in item.get("imports", []):
            module_name = declaration["module"]
            if module_name.startswith("."):
                # Resolve relative import by the declaring module's package.
                dots = len(module_name) - len(module_name.lstrip("."))
                remainder = module_name[dots:]
                parts = path.removeprefix("backend/").split("/")[:-1]
                parent = parts[:max(0, len(parts) - (dots - 1))]
                module_name = ".".join(parent + ([remainder] if remainder else []))
            for candidate in (
                "backend/" + module_name.replace(".", "/") + ".py",
                "backend/" + module_name.replace(".", "/") + "/__init__.py",
            ):
                if candidate in by_path and candidate != path:
                    targets.add(candidate)
        item["resolved_local_imports"] = sorted(targets)
        for target in targets:
            imported_by[target].add(path)
    for item in modules:
        item["imported_by"] = sorted(imported_by[item["path"]])
    counts = Counter(item["bucket"] for item in modules)
    valid_review_count = sum(item["review_status"] == "verified_reviewed" for item in modules)
    stale_review_count = sum(item["review_status"] == "stale_review" for item in modules)
    return {"schema_version": 2, "scope": list(TOP), "generated_from": "current_worktree",
            "method": "AST Python symbols, static local imports/reverse edges, SHA-verified review status; path/hash for other languages",
            "file_count": len(modules), "python_count": sum(m["path"].endswith(".py") for m in modules),
            "definition_count": sum(len(m.get("definitions", [])) for m in modules),
            "reviewed_file_count": valid_review_count,
            "stale_review_file_count": stale_review_count,
            "line_by_line_review_percent": round(100 * valid_review_count / len(modules), 2) if modules else 0,
            "bucket_counts": dict(sorted(counts.items())), "files": modules}

def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args=parser.parse_args()
    actual=generate()
    if args.check:
        expected=json.loads(OUTPUT.read_text(encoding="utf-8"))
        assert actual == expected, "Repository inventory is stale. Regenerate after source changes."
    else:
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_text(json.dumps(actual, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
    print(json.dumps({k:v for k,v in actual.items() if k!="files"}, indent=2))

if __name__=="__main__":
    main()
