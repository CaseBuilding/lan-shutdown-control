from __future__ import annotations

import json
import secrets
from dataclasses import asdict, dataclass
from pathlib import Path


def generate_access_token() -> str:
    return secrets.token_urlsafe(24)


@dataclass
class AppConfig:
    port: int = 8765
    access_token: str = ""
    auto_start: bool = True
    start_with_windows: bool = False
    shutdown_delay_seconds: int = 15
    bind_host: str = "0.0.0.0"

    def ensure_defaults(self) -> None:
        if not self.access_token:
            self.access_token = generate_access_token()


class ConfigManager:
    def __init__(self, config_path: Path | None = None) -> None:
        self.config_path = config_path or Path(__file__).resolve().parent / "config.json"
        self.config = AppConfig()
        self.load()

    def load(self) -> AppConfig:
        if self.config_path.exists():
            with self.config_path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
            self.config = AppConfig(**data)
        self.config.ensure_defaults()
        return self.config

    def save(self) -> None:
        self.config.ensure_defaults()
        with self.config_path.open("w", encoding="utf-8") as handle:
            json.dump(asdict(self.config), handle, indent=2, ensure_ascii=False)

    def update(self, **kwargs) -> AppConfig:
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
        self.save()
        return self.config
