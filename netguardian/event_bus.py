from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from typing import Any


class EventDispatcher:
    def __init__(self) -> None:
        self._handlers: dict[str, list[Callable[[dict[str, Any]], None]]] = defaultdict(list)

    def subscribe(self, event_type: str, handler: Callable[[dict[str, Any]], None]) -> None:
        self._handlers[event_type].append(handler)

    def publish(self, event: dict[str, Any]) -> None:
        for handler in self._handlers.get(event["event_type"], []):
            handler(event)
        for handler in self._handlers.get("*", []):
            handler(event)

