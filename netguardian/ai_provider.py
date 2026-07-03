from __future__ import annotations

import json
import os
from typing import Any

from .config import (
    ai_mode,
    ai_provider,
    gemini_model,
    gemini_timeout_seconds,
    ollama_model,
    ollama_timeout_seconds,
    ollama_url,
)


class LiveAIUnavailable(RuntimeError):
    pass


def agent_mode() -> dict[str, str | bool]:
    configured = ai_mode()
    provider = ai_provider()
    live_available = _provider_available(provider)
    live_enabled = configured == "live" or (configured == "auto" and live_available)
    return {
        "configured": configured,
        "provider": provider,
        "active": _active_name(provider) if live_enabled else "deterministic",
        "live_available": live_available,
        "model": _provider_model(provider) if live_enabled else "deterministic-fallback",
    }


def live_ai_enabled() -> bool:
    mode = ai_mode()
    provider = ai_provider()
    return mode == "live" or (mode == "auto" and _provider_available(provider))


def generate_json(task: str, bundle: dict[str, Any], schema: dict[str, str]) -> dict[str, Any]:
    if not live_ai_enabled():
        raise LiveAIUnavailable("live_ai_disabled")
    provider = ai_provider()
    if provider == "ollama":
        return _generate_ollama_json(task, bundle, schema)
    if provider == "gemini":
        return _generate_gemini_json(task, bundle, schema)
    raise LiveAIUnavailable(f"unknown_ai_provider_{provider}")


def _generate_gemini_json(task: str, bundle: dict[str, Any], schema: dict[str, str]) -> dict[str, Any]:
    key = _api_key()
    if not key:
        raise LiveAIUnavailable("missing_api_key")
    try:
        import requests
    except ModuleNotFoundError as exc:
        raise LiveAIUnavailable("requests_not_installed") from exc

    prompt = _build_prompt(task, bundle, schema)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{gemini_model()}:generateContent"
    response = requests.post(
        url,
        params={"key": key},
        json={
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.25,
                "responseMimeType": "application/json",
            },
        },
        timeout=gemini_timeout_seconds(),
    )
    if response.status_code >= 400:
        raise LiveAIUnavailable(_gemini_error_reason(response.status_code))
    payload = response.json()
    try:
        text = payload["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError, TypeError) as exc:
        raise LiveAIUnavailable("invalid_gemini_response") from exc
    return _parse_json_object(text, "invalid_gemini_json")


def _generate_ollama_json(task: str, bundle: dict[str, Any], schema: dict[str, str]) -> dict[str, Any]:
    try:
        import requests
    except ModuleNotFoundError as exc:
        raise LiveAIUnavailable("requests_not_installed") from exc

    prompt = _build_prompt(task, bundle, schema)
    response = requests.post(
        f"{ollama_url()}/api/generate",
        json={
            "model": ollama_model(),
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {"temperature": 0.2},
        },
        timeout=ollama_timeout_seconds(),
    )
    if response.status_code >= 400:
        raise LiveAIUnavailable(_ollama_error_reason(response.status_code))
    payload = response.json()
    text = payload.get("response")
    if not isinstance(text, str):
        raise LiveAIUnavailable("invalid_ollama_response")
    return _parse_json_object(text, "invalid_ollama_json")


def _api_key() -> str:
    return os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY") or ""


def _provider_available(provider: str) -> bool:
    if provider == "gemini":
        return bool(_api_key())
    if provider == "ollama":
        try:
            import requests
        except ModuleNotFoundError:
            return False
        try:
            response = requests.get(f"{ollama_url()}/api/tags", timeout=0.75)
        except requests.RequestException:
            return False
        return response.status_code < 400
    return False


def _active_name(provider: str) -> str:
    if provider == "ollama":
        return "local_ollama"
    if provider == "gemini":
        return "live_gemini"
    return f"live_{provider}"


def _provider_model(provider: str) -> str:
    if provider == "ollama":
        return ollama_model()
    if provider == "gemini":
        return gemini_model()
    return "unknown-model"


def _build_prompt(task: str, bundle: dict[str, Any], schema: dict[str, str]) -> str:
    safe_bundle = {
        "incident": bundle.get("incident"),
        "device": bundle.get("device"),
        "owner": bundle.get("owner"),
        "critical_assets": bundle.get("critical_assets"),
        "relationships": bundle.get("relationships"),
        "evidence": bundle.get("evidence"),
        "telemetry_events": bundle.get("telemetry_events"),
        "actions": bundle.get("actions"),
        "approvals": bundle.get("approvals"),
    }
    return (
        "You are NetGuardian's SOC agent. Analyze only the JSON enterprise state below. "
        "Do not invent telemetry, assets, actions, approvals, or execution results. "
        "Do not claim an action was executed unless it appears in actions. "
        "Do not bypass human approval. "
        "Return only valid JSON matching the requested keys.\n\n"
        f"Task: {task}\n\n"
        f"Required JSON keys and meanings:\n{json.dumps(schema, indent=2)}\n\n"
        f"Enterprise state:\n{json.dumps(safe_bundle, indent=2)}"
    )


def _gemini_error_reason(status_code: int) -> str:
    if status_code == 400:
        return "gemini_bad_request"
    if status_code == 401:
        return "gemini_api_key_invalid"
    if status_code == 403:
        return "gemini_api_access_denied"
    if status_code == 429:
        return "gemini_quota_or_rate_limit"
    return f"gemini_error_{status_code}"


def _ollama_error_reason(status_code: int) -> str:
    if status_code == 404:
        return "ollama_model_not_found"
    if status_code == 503:
        return "ollama_model_unavailable"
    return f"ollama_error_{status_code}"


def _parse_json_object(text: str, error_reason: str) -> dict[str, Any]:
    try:
        result = json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise LiveAIUnavailable(error_reason)
        try:
            result = json.loads(text[start : end + 1])
        except json.JSONDecodeError as exc:
            raise LiveAIUnavailable(error_reason) from exc
    if not isinstance(result, dict):
        raise LiveAIUnavailable(error_reason)
    return result
