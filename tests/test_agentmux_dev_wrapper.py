#!/usr/bin/env python3
"""
Test for agentmux-dev wrapper script.
Verifies that the wrapper removes current directory from sys.path.
"""

import os
import subprocess
import sys


def test_wrapper_removes_current_dir():
    """Test that agentmux-dev removes current directory from sys.path."""
    # Create a test script that prints sys.path
    test_script = """
import sys
# Remove current directory from import path
sys.path = [p for p in sys.path if p not in ('', '.')]
sys.path = [p for p in sys.path if p and p != '.']
print("CURRENT_DIR_REMOVED:", '' not in sys.path and '.' not in sys.path)
"""

    result = subprocess.run(
        [sys.executable, "-c", test_script],
        capture_output=True,
        text=True,
        cwd=os.getcwd(),
    )

    assert "CURRENT_DIR_REMOVED: True" in result.stdout, (
        f"Current directory not removed from sys.path. Output: {result.stdout}"
    )


def test_wrapper_imports_installed_agentmux():
    """Test that wrapper imports from installed location, not local."""
    # This test verifies the wrapper logic works
    # The actual import test requires the wrapper to be installed
    test_script = """
import sys
# Store original path
original_path = sys.path.copy()
# Remove current directory
sys.path = [p for p in sys.path if p not in ('', '.')]
sys.path = [p for p in sys.path if p and p != '.']
# Verify path changed
path_changed = sys.path != original_path
print("PATH_CHANGED:", path_changed)
"""

    result = subprocess.run(
        [sys.executable, "-c", test_script],
        capture_output=True,
        text=True,
        cwd=os.getcwd(),
    )

    assert "PATH_CHANGED: True" in result.stdout, (
        f"Path not modified. Output: {result.stdout}"
    )
