"""Persistent local configuration for opensiri-ai."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path


DEFAULT_CONFIG_PATH = Path.home() / ".config" / "opensiri-ai" / "config.json"


@dataclass
class SourceConfig:
    read: bool = False
    write: bool = False
    max_sensitivity: str = "high"


@dataclass
class HarnessConfig:
    model_url: str = "http://127.0.0.1:8081"
    model_name: str = "default_model"
    audit_path: str = "~/.local/share/opensiri-ai/audit.jsonl"
    transcript_dir: str = "~/.local/share/opensiri-ai/transcripts"
    network_enabled: bool = False
    sources: dict[str, SourceConfig] = field(default_factory=lambda: {
        "hypersave": SourceConfig(read=False, write=False),
        "files": SourceConfig(read=False, write=False),
        "finder": SourceConfig(read=False, write=False),
        "calendar": SourceConfig(read=False, write=False),
        "contacts": SourceConfig(read=False, write=False),
        "notes": SourceConfig(read=False, write=False),
        "reminders": SourceConfig(read=False, write=False),
        "mail": SourceConfig(read=False, write=False),
        "maps": SourceConfig(read=False, write=False),
        "messages": SourceConfig(read=False, write=False),
        "messages_index": SourceConfig(read=False, write=False),
        "music": SourceConfig(read=False, write=False),
        "podcasts": SourceConfig(read=False, write=False),
        "safari": SourceConfig(read=False, write=False),
        "photos": SourceConfig(read=False, write=False),
        "visual": SourceConfig(read=False, write=False),
        "web": SourceConfig(read=False, write=False),
        "browser": SourceConfig(read=False, write=False),
        "system": SourceConfig(read=False, write=False),
    })


def load_config(path: str | Path = DEFAULT_CONFIG_PATH) -> HarnessConfig:
    p = Path(path).expanduser()
    if not p.exists():
        cfg = HarnessConfig()
        save_config(cfg, p)
        return cfg
    raw = json.loads(p.read_text())
    sources = {k: SourceConfig(**v) for k, v in raw.get("sources", {}).items()}
    cfg = HarnessConfig(**{k: v for k, v in raw.items() if k != "sources"})
    cfg.sources.update(sources)
    return cfg


def save_config(config: HarnessConfig, path: str | Path = DEFAULT_CONFIG_PATH) -> None:
    p = Path(path).expanduser()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(asdict(config), indent=2))
