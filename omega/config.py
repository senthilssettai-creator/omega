from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, Field


load_dotenv()


class OmegaSettings(BaseModel):
    """Runtime configuration loaded from environment variables."""

    home_dir: Path = Field(default_factory=lambda: Path(os.getenv("OMEGA_HOME", ".omega")))
    workspace: Path = Field(default_factory=lambda: Path(os.getenv("OMEGA_WORKSPACE", ".")))
    log_level: str = Field(default_factory=lambda: os.getenv("OMEGA_LOG_LEVEL", "INFO"))
    openrouter_api_key: str | None = Field(default_factory=lambda: os.getenv("OPENROUTER_API_KEY"))
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    permission_file: Path = Field(
        default_factory=lambda: Path(os.getenv("OMEGA_PERMISSION_FILE", "config/permissions.json"))
    )
    model_file: Path = Field(default_factory=lambda: Path(os.getenv("OMEGA_MODEL_FILE", "config/models.json")))
    max_parallel_agents: int = Field(default_factory=lambda: int(os.getenv("OMEGA_MAX_PARALLEL_AGENTS", "4")))
    command_timeout_seconds: int = Field(default_factory=lambda: int(os.getenv("OMEGA_COMMAND_TIMEOUT", "60")))
    github_token: str | None = Field(default_factory=lambda: os.getenv("GITHUB_TOKEN"))
    slack_webhook_url: str | None = Field(default_factory=lambda: os.getenv("SLACK_WEBHOOK_URL"))
    slack_bot_token: str | None = Field(default_factory=lambda: os.getenv("SLACK_BOT_TOKEN"))
    google_drive_token: str | None = Field(default_factory=lambda: os.getenv("GOOGLE_DRIVE_TOKEN"))
    require_approval_default: bool = True

    @property
    def data_dir(self) -> Path:
        return self.home_dir / "data"

    @property
    def logs_dir(self) -> Path:
        return self.home_dir / "logs"

    @property
    def plugins_dir(self) -> Path:
        return self.home_dir / "plugins"

    @property
    def workflows_dir(self) -> Path:
        return self.home_dir / "workflows"

    @property
    def memory_db_path(self) -> Path:
        return self.data_dir / "omega.sqlite3"

    @property
    def mcp_config_path(self) -> Path:
        return self.home_dir / "mcp_servers.json"

    def ensure_directories(self) -> None:
        for path in [self.home_dir, self.data_dir, self.logs_dir, self.plugins_dir, self.workflows_dir]:
            path.mkdir(parents=True, exist_ok=True)

    def resolved_workspace(self) -> Path:
        return self.workspace.expanduser().resolve()


def load_settings() -> OmegaSettings:
    settings = OmegaSettings()
    settings.ensure_directories()
    return settings
