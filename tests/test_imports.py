"""Smoke tests to verify all top-level subpackages can be imported independently.

These tests catch circular imports and missing dependencies that can be masked
when the full test suite is run (due to import ordering side effects).
"""

import os
import subprocess
import sys


def _import_in_isolation(module: str) -> None:
    """Import a module in a fresh Python process to detect circular imports."""
    # Ensure the subprocess can find the package (src layout).
    src_dir = os.path.join(os.path.dirname(__file__), "..", "src")
    env = os.environ.copy()
    pythonpath = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = os.pathsep.join(filter(None, [src_dir, pythonpath]))

    result = subprocess.run(
        [sys.executable, "-c", f"import {module}"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0, (
        f"Failed to import {module!r} in isolation:\n{result.stderr}"
    )


def test_import_monitor():
    _import_in_isolation("agentmux.monitor")


def test_import_workflow():
    _import_in_isolation("agentmux.workflow")


def test_import_pipeline():
    _import_in_isolation("agentmux.pipeline")


def test_import_configuration():
    _import_in_isolation("agentmux.configuration")


def test_import_runtime():
    _import_in_isolation("agentmux.runtime")


def test_import_sessions():
    _import_in_isolation("agentmux.sessions")


def test_import_integrations():
    _import_in_isolation("agentmux.integrations")
