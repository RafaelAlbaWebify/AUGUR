from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AUGUR"
    environment: str = "local"

    model_config = SettingsConfigDict(
        env_prefix="AUGUR_",
        case_sensitive=False,
    )

    @property
    def project_root(self) -> Path:
        return Path(__file__).resolve().parents[3]

    @property
    def data_dir(self) -> Path:
        path = self.project_root / "data"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def sqlite_path(self) -> Path:
        return self.data_dir / "augur_app.sqlite"

    @property
    def duckdb_path(self) -> Path:
        return self.data_dir / "augur_analytics.duckdb"


settings = Settings()
