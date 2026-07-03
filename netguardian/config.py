from __future__ import annotations

import os
from pathlib import Path


def db_path() -> Path:
    return Path(os.getenv("NETGUARDIAN_DB_PATH", "data/netguardian.db"))


def ensure_data_dir() -> None:
    db_path().parent.mkdir(parents=True, exist_ok=True)


def ai_mode() -> str:
    return os.getenv("NETGUARDIAN_AI_MODE", "auto").strip().lower()


def ai_provider() -> str:
    return os.getenv("NETGUARDIAN_AI_PROVIDER", "ollama").strip().lower()


def gemini_model() -> str:
    return os.getenv("NETGUARDIAN_GEMINI_MODEL", "gemini-2.0-flash")


def gemini_timeout_seconds() -> float:
    return float(os.getenv("NETGUARDIAN_GEMINI_TIMEOUT_SECONDS", "30"))


def ollama_url() -> str:
    return os.getenv("NETGUARDIAN_OLLAMA_URL", "http://127.0.0.1:11434").strip().rstrip("/")


def ollama_model() -> str:
    return os.getenv("NETGUARDIAN_OLLAMA_MODEL", "qwen2.5:7b").strip()


def ollama_timeout_seconds() -> float:
    return float(os.getenv("NETGUARDIAN_OLLAMA_TIMEOUT_SECONDS", "120"))
