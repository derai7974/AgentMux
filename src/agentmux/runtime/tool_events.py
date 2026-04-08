"""Tool-call event logging and event source for the session event bus.

This module provides:
- ``append_tool_event()`` — append a structured JSON line to
  ``tool_events.jsonl`` so that downstream consumers (MCP submit tools,
  the orchestrator) can observe tool invocations.
- ``ToolCallEventSource`` — an ``EventSource`` that seeds existing entries
  from ``tool_events.jsonl`` and tails the file via watchdog, publishing
  ``SessionEvent(kind="tool.<name>", source="tool_call", ...)`` to the bus.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from .event_bus import EventBus, EventSource, SessionEvent

logger = logging.getLogger(__name__)

TOOL_EVENTS_LOG_NAME = "tool_events.jsonl"


def append_tool_event(
    log_path: Path,
    tool_name: str,
    payload: dict[str, Any],
) -> None:
    """Append one JSON line to *log_path* describing a tool call.

    Creates parent directories if they do not exist.  Subsequent calls
    append without truncating.
    """
    entry = {
        "tool": tool_name,
        "timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
        "payload": payload,
    }
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


class ToolCallEventSource(EventSource):
    """Watch ``tool_events.jsonl`` and emit ``SessionEvent`` objects.

    On ``start()`` the source seeds any pre-existing lines, then tails
    the file for new appends via a watchdog observer.
    """

    def __init__(self, feature_dir: Path) -> None:
        self._feature_dir = feature_dir.resolve()
        self._offset = 0
        self._observer: Any = None

    def start(self, bus: EventBus) -> None:
        from .file_events import ensure_watchdog_available

        ensure_watchdog_available()

        self._seed_existing(bus)

        from watchdog.events import FileSystemEvent, FileSystemEventHandler
        from watchdog.observers import Observer

        class _ToolLogHandler(FileSystemEventHandler):
            def __init__(self, source: ToolCallEventSource, bus: EventBus) -> None:
                super().__init__()
                self._source = source
                self._bus = bus

            def on_any_event(self, event: FileSystemEvent) -> None:
                if getattr(event, "is_directory", False):
                    return
                src = getattr(event, "src_path", "")
                if Path(src).name != TOOL_EVENTS_LOG_NAME:
                    return
                self._source._on_modified(self._bus)

        observer = Observer()
        observer.schedule(
            _ToolLogHandler(self, bus),
            str(self._feature_dir),
            recursive=False,
        )
        observer.start()
        self._observer = observer

    def stop(self) -> None:
        if self._observer is None:
            return
        self._observer.stop()
        self._observer.join()
        self._observer = None

    def _seed_existing(self, bus: EventBus) -> None:
        log_path = self._feature_dir / TOOL_EVENTS_LOG_NAME
        if not log_path.exists():
            return

        text = log_path.read_text(encoding="utf-8")
        lines = text.splitlines()
        for line in lines:
            self._emit_line(line, bus)
        self._offset = log_path.stat().st_size

    def _on_modified(self, bus: EventBus) -> None:
        log_path = self._feature_dir / TOOL_EVENTS_LOG_NAME
        if not log_path.exists():
            return

        current_size = log_path.stat().st_size
        if current_size <= self._offset:
            return

        with log_path.open("r", encoding="utf-8") as f:
            f.seek(self._offset)
            for line in f:
                stripped = line.rstrip("\n")
                if stripped:
                    self._emit_line(stripped, bus)
            self._offset = f.tell()

    def _emit_line(self, line: str, bus: EventBus) -> None:
        try:
            entry = json.loads(line)
        except (json.JSONDecodeError, ValueError):
            logger.warning("Skipping malformed tool event line: %s", line[:120])
            return

        tool_name = entry.get("tool", "unknown")
        bus.publish(
            SessionEvent(
                kind=f"tool.{tool_name}",
                source="tool_call",
                payload=entry,
            )
        )
