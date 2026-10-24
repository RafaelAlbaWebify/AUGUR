"""AUGUR configuration contract on disposable paths, never operator data."""
from pathlib import Path

from app.core.config import Settings


def test_local_database_paths_resolve_inside_isolated_project(tmp_path, monkeypatch):
    monkeypatch.setattr(Settings, "project_root", property(lambda self: tmp_path))
    config = Settings(_env_file=None)
    assert config.data_dir == tmp_path / "data"
    assert config.sqlite_path == tmp_path / "data" / "augur_app.sqlite"
    assert config.duckdb_path == tmp_path / "data" / "augur_analytics.duckdb"
    assert config.data_dir.is_dir()
    assert not config.sqlite_path.exists()
    assert not config.duckdb_path.exists()


def test_environment_setting_is_read_without_database_creation(tmp_path, monkeypatch):
    monkeypatch.setenv("AUGUR_ENVIRONMENT", "test")
    monkeypatch.setattr(Settings, "project_root", property(lambda self: tmp_path))
    config = Settings(_env_file=None)
    assert config.environment == "test"
    assert not (tmp_path / "data").exists()
