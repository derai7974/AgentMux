#!/usr/bin/env python3
"""Control pane monitor for the multi-agent pipeline."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

RESET = "\033[0m"
BOLD = "\033[1m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
CYAN = "\033[36m"
DIM = "\033[2m"


def get_terminal_size() -> tuple[int, int]:
    try:
        size = os.get_terminal_size()
        return size.columns, size.lines
    except OSError:
        return 40, 24


def get_active_roles(session_name: str, panes_path: Path) -> set[str]:
    """Return the set of agent roles that have a live tmux pane."""
    try:
        panes = json.loads(panes_path.read_text(encoding="utf-8"))
    except Exception:
        return set()

    try:
        result = subprocess.run(
            ["tmux", "list-panes", "-t", f"{session_name}:pipeline", "-F", "#{pane_id}"],
            capture_output=True,
            text=True,
            check=False,
        )
        live_ids = {t.strip() for t in result.stdout.splitlines() if t.strip()}
    except Exception:
        return set()

    active: set[str] = set()
    for role, pane_id in panes.items():
        if role.startswith("_") or pane_id is None:
            continue
        if pane_id in live_ids:
            # Normalize parallel coder keys (coder_1, coder_2, ...) to "coder"
            base_role = role.split("_")[0] if role.startswith("coder_") else role
            active.add(base_role)
    return active


def load_state(state_path: Path) -> dict:
    try:
        text = state_path.read_text(encoding="utf-8").strip()
        if text:
            return json.loads(text)
    except Exception:
        pass
    return {}


def status_color(status: str) -> str:
    if status in ("completion_approved",):
        return GREEN
    if status in ("failed",):
        return RED
    if status in ("completion_pending", "review_ready"):
        return YELLOW
    return CYAN


def _trim_model(model: str, cli: str) -> str:
    """Strip vendor prefix matching CLI name, then truncate to 8 chars."""
    prefix = f"{cli}-"
    if model.lower().startswith(prefix.lower()):
        model = model[len(prefix) :]
    return model[:8]


def _format_log_entry(raw_line: str) -> str:
    parts = raw_line.split()
    if len(parts) < 3:
        return raw_line[:20]
    time_part = parts[1][:5]
    status_part = parts[2][:14]
    return f"{time_part} {status_part}"


def render(
    session_name: str,
    state_path: Path,
    panes_path: Path,
    agents: dict[str, dict[str, str]],
    width: int,
    height: int,
    start_time: float,
) -> str:
    state = load_state(state_path)
    active_roles = get_active_roles(session_name, panes_path)

    status = state.get("status", "waiting...")
    active_role = state.get("active_role", "")
    review_iter = state.get("review_iteration", 0)
    subplan_count = state.get("subplan_count", 0)

    lines: list[str] = []

    lines.append(f"{BOLD}{CYAN}Multi-Agent Pipeline{RESET}")
    lines.append("\u2500" * (width - 1))
    lines.append("")

    lines.append(f"{BOLD}Pipeline{RESET}")
    color = status_color(status)
    lines.append(f"  {color}{status[:17]}{RESET}")

    if review_iter:
        lines.append(f"  {DIM}review iter {review_iter}{RESET}")
    if subplan_count > 1:
        lines.append(f"  {DIM}{subplan_count} subplans{RESET}")

    lines.append("")
    lines.append("\u2500" * (width - 1))
    lines.append("")

    lines.append(f"{BOLD}Agents{RESET}")
    lines.append("")

    for role, cfg in agents.items():
        is_active = role in active_roles
        if is_active:
            bullet = f"{GREEN}\u25cf{RESET}"
            state_label = f"{GREEN}ACTV{RESET}"
        else:
            bullet = f"{DIM}\u25cb{RESET}"
            state_label = f"{DIM}IDLE{RESET}"

        is_current = role == active_role
        if is_current:
            name_part = f"{BOLD}{role:<10}{RESET}"
        else:
            name_part = f"{role:<10}"
        lines.append(f"  {bullet} {name_part} {state_label}")

        cli = cfg.get("cli", "?")
        model = _trim_model(cfg.get("model", ""), cli)
        lines.append(f"    {DIM}{cli}/{model}{RESET}")
        lines.append("")

    status_log_path = state_path.parent / "status_log.txt"
    status_log_lines: list[str] = []
    try:
        status_log_lines = [
            line.rstrip("\n")
            for line in status_log_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
    except Exception:
        status_log_lines = []

    elapsed_seconds = max(0, int(time.time() - start_time))
    hours = elapsed_seconds // 3600
    minutes = (elapsed_seconds % 3600) // 60
    seconds = elapsed_seconds % 60
    elapsed_str = f"{hours}:{minutes:02d}:{seconds:02d}"

    footer = ["\u2500" * (width - 1), f"{DIM}↑ {elapsed_str}{RESET}"]

    if status_log_lines:
        available_log_lines = max(0, height - len(lines) - len(footer) - 1)
        lines.append(f"{BOLD}Log{RESET}")
        for entry in status_log_lines[-available_log_lines:]:
            lines.append(f"{DIM}{_format_log_entry(entry)}{RESET}")

    lines.extend(footer)

    while len(lines) < height - 1:
        lines.append("")

    return "\n".join(lines[:height])


def append_status_change(log_path: Path, prev_status: str | None, status: str) -> str | None:
    if not status:
        return prev_status
    if status == prev_status:
        return prev_status

    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(f"{ts}  {status}\n")
    return status


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--feature-dir", required=True)
    parser.add_argument("--session-name", required=True)
    parser.add_argument("--config", required=True)
    args = parser.parse_args()

    feature_dir = Path(args.feature_dir)
    state_path = feature_dir / "state.json"
    panes_path = feature_dir / "panes.json"
    config_path = Path(args.config)

    raw = json.loads(config_path.read_text(encoding="utf-8"))
    agents: dict[str, dict[str, str]] = {}
    for role in ("architect", "coder", "designer", "docs"):
        if role in raw:
            agents[role] = {"cli": raw[role]["cli"], "model": raw[role].get("model", "")}

    start_time = time.time()
    status_log_path = feature_dir / "status_log.txt"
    prev_status: str | None = None

    sys.stdout.write("\033[?25l")
    sys.stdout.flush()

    try:
        while True:
            width, height = get_terminal_size()
            output = render(args.session_name, state_path, panes_path, agents, width, height, start_time)
            sys.stdout.write("\033[H\033[2J" + output)
            sys.stdout.flush()
            state = load_state(state_path)
            prev_status = append_status_change(status_log_path, prev_status, state.get("status", ""))
            time.sleep(1.0)
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write("\033[?25h")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
