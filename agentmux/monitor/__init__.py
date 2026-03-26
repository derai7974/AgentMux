#!/usr/bin/env python3
"""Control pane monitor for the multi-agent pipeline."""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

from ..configuration import infer_project_dir, load_layered_config
from ..terminal_ui.layout import MONITOR_WIDTH
from . import render as render_module
from . import state_reader as state_reader_module
from .render import RESET, WHITE, _ANSI_RE, render
from .state_reader import PIPELINE_STATES, get_role_states, load_state


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
    parser.add_argument("--config")
    args = parser.parse_args()

    feature_dir = Path(args.feature_dir)
    state_path = feature_dir / "state.json"
    runtime_state_path = feature_dir / "runtime_state.json"
    config_path = Path(args.config).resolve() if args.config else None

    loaded = load_layered_config(
        infer_project_dir(feature_dir),
        explicit_config_path=config_path,
    )
    agents = {
        role: {"cli": agent.cli, "model": agent.model}
        for role, agent in loaded.agents.items()
    }

    start_time = time.time()
    status_log_path = feature_dir / "status_log.txt"
    prev_status: str | None = None

    sys.stdout.write("\033[?25l")
    sys.stdout.flush()

    try:
        while True:
            width, height = os.get_terminal_size()
            if width != MONITOR_WIDTH:
                own_pane = os.environ.get("TMUX_PANE", "")
                if own_pane:
                    subprocess.run(
                        ["tmux", "resize-pane", "-t", own_pane, "-x", str(MONITOR_WIDTH)],
                        check=False,
                    )
                    width, height = os.get_terminal_size()
            output = render(
                session_name=args.session_name,
                state_path=state_path,
                runtime_state_path=runtime_state_path,
                agents=agents,
                width=width,
                height=height,
                start_time=start_time,
                log_path=status_log_path,
            )
            sys.stdout.write("\033[H\033[2J" + output)
            sys.stdout.flush()
            state = load_state(state_path)
            prev_status = append_status_change(status_log_path, prev_status, state.get("phase", ""))
            time.sleep(1.0)
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write("\033[?25h")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
