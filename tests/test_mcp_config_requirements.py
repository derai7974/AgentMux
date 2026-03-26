from __future__ import annotations

import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agentmux.integrations.mcp import McpServerSpec, cleanup_mcp, ensure_mcp_config, setup_mcp
from agentmux.shared.models import AgentConfig


class McpConfigRequirementsTests(unittest.TestCase):
    def _server(self) -> McpServerSpec:
        return McpServerSpec(name="agentmux-research", module="agentmux.integrations.mcp_research_server", env={})

    def test_setup_mcp_adds_pythonpath_for_selected_roles(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tmp_path = Path(td)
            feature_dir = tmp_path / "feature"
            project_dir = tmp_path / "project"
            feature_dir.mkdir()
            project_dir.mkdir()
            agents = {
                "architect": AgentConfig(role="architect", cli="codex", model="gpt-5.3-codex", args=["-a", "never"]),
                "product-manager": AgentConfig(role="product-manager", cli="claude", model="opus", args=[]),
                "reviewer": AgentConfig(role="reviewer", cli="claude", model="sonnet", args=[]),
            }

            updated = setup_mcp(
                agents,
                [self._server()],
                ["architect", "product-manager"],
                feature_dir,
                project_dir,
            )

            self.assertEqual(str(project_dir), updated["architect"].env["PYTHONPATH"])
            self.assertEqual(str(project_dir), updated["product-manager"].env["PYTHONPATH"])
            self.assertIsNone(updated["reviewer"].env)

    def test_setup_mcp_prepends_existing_pythonpath(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tmp_path = Path(td)
            feature_dir = tmp_path / "feature"
            project_dir = tmp_path / "project"
            feature_dir.mkdir()
            project_dir.mkdir()
            agent = AgentConfig(
                role="architect",
                cli="claude",
                model="opus",
                env={"PYTHONPATH": "/existing/path"},
            )

            updated = setup_mcp(
                {"architect": agent},
                [self._server()],
                ["architect"],
                feature_dir,
                project_dir,
            )

            self.assertEqual(
                os.pathsep.join([str(project_dir), "/existing/path"]),
                updated["architect"].env["PYTHONPATH"],
            )

    def test_ensure_mcp_config_writes_claude_project_config(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            project_dir = Path(td)
            config_path = project_dir / ".claude" / "settings.json"
            config_path.parent.mkdir(parents=True)
            config_path.write_text('{"existing": true}\n', encoding="utf-8")
            agents = {
                "architect": AgentConfig(role="architect", cli="claude", model="opus", provider="claude"),
            }

            ensure_mcp_config(
                agents,
                [self._server()],
                ["architect"],
                project_dir,
                interactive=True,
                confirm=lambda _message: True,
            )

            config = json.loads(config_path.read_text(encoding="utf-8"))
            server = config["mcpServers"]["agentmux-research"]
            self.assertTrue(config["existing"])
            self.assertEqual("stdio", server["type"])
            self.assertEqual(sys.executable, server["command"])
            self.assertEqual(["-m", "agentmux.integrations.mcp_research_server"], server["args"])

    def test_ensure_mcp_config_writes_gemini_project_config(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            project_dir = Path(td)
            agents = {
                "product-manager": AgentConfig(
                    role="product-manager",
                    cli="gemini",
                    model="gemini-2.5-pro",
                    provider="gemini",
                ),
            }

            ensure_mcp_config(
                agents,
                [self._server()],
                ["product-manager"],
                project_dir,
                interactive=True,
                confirm=lambda _message: True,
            )

            config = json.loads((project_dir / ".gemini" / "settings.json").read_text(encoding="utf-8"))
            server = config["mcpServers"]["agentmux-research"]
            self.assertEqual(sys.executable, server["command"])
            self.assertEqual(["-m", "agentmux.integrations.mcp_research_server"], server["args"])
            self.assertTrue(server["trust"])

    def test_ensure_mcp_config_writes_opencode_project_config(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            project_dir = Path(td)
            config_path = project_dir / "opencode.json"
            config_path.write_text('{"tools": {"x": true}}\n', encoding="utf-8")
            agents = {
                "architect": AgentConfig(role="architect", cli="opencode", model="sonnet", provider="opencode"),
            }

            ensure_mcp_config(
                agents,
                [self._server()],
                ["architect"],
                project_dir,
                interactive=True,
                confirm=lambda _message: True,
            )

            config = json.loads(config_path.read_text(encoding="utf-8"))
            server = config["mcp"]["agentmux-research"]
            self.assertEqual({"x": True}, config["tools"])
            self.assertEqual("local", server["type"])
            self.assertEqual([sys.executable, "-m", "agentmux.integrations.mcp_research_server"], server["command"])
            self.assertTrue(server["enabled"])

    def test_ensure_mcp_config_writes_codex_user_config_and_refreshes_existing_block(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            home_dir = Path(td)
            project_dir = home_dir / "project"
            project_dir.mkdir()
            config_path = home_dir / ".codex" / "config.toml"
            config_path.parent.mkdir(parents=True)
            config_path.write_text(
                'foo = "bar"\n\n'
                '[mcp_servers.agentmux-research]\n'
                'command = "python3"\n'
                'args = ["-m", "agentmux.integrations.mcp_research_server"]\n'
                'enabled = true\n\n'
                '[mcp_servers.agentmux-research.env]\n'
                'FEATURE_DIR = "/old/feature"\n',
                encoding="utf-8",
            )
            agents = {
                "architect": AgentConfig(role="architect", cli="codex", model="gpt-5.3-codex", provider="codex"),
            }

            with patch("agentmux.integrations.mcp.Path.home", return_value=home_dir):
                ensure_mcp_config(
                    agents,
                    [self._server()],
                    ["architect"],
                    project_dir,
                    interactive=True,
                    confirm=lambda _message: True,
                )

            content = config_path.read_text(encoding="utf-8")
            self.assertIn('foo = "bar"', content)
            self.assertIn(f'command = "{sys.executable}"', content)
            self.assertIn('args = ["-m", "agentmux.integrations.mcp_research_server"]', content)
            self.assertEqual(1, content.count("[mcp_servers.agentmux-research]"))
            self.assertNotIn('FEATURE_DIR = "/old/feature"', content)

    def test_ensure_mcp_config_warns_when_noninteractive_and_missing(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            home_dir = Path(td)
            project_dir = home_dir / "project"
            project_dir.mkdir()
            agents = {
                "architect": AgentConfig(role="architect", cli="codex", model="gpt-5.3-codex", provider="codex"),
            }
            output = io.StringIO()

            with patch("agentmux.integrations.mcp.Path.home", return_value=home_dir):
                ensure_mcp_config(
                    agents,
                    [self._server()],
                    ["architect"],
                    project_dir,
                    interactive=False,
                    output=output,
                )

            self.assertIn("Missing MCP config for codex", output.getvalue())
            self.assertFalse((home_dir / ".codex" / "config.toml").exists())

    def test_ensure_mcp_config_dedupes_shared_provider_prompt(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            project_dir = Path(td)
            agents = {
                "architect": AgentConfig(role="architect", cli="claude", model="opus", provider="claude"),
                "product-manager": AgentConfig(role="product-manager", cli="claude", model="opus", provider="claude"),
            }
            prompts: list[str] = []

            ensure_mcp_config(
                agents,
                [self._server()],
                ["architect", "product-manager"],
                project_dir,
                interactive=True,
                confirm=lambda message: prompts.append(message) or True,
            )

            self.assertEqual(1, len(prompts))
            self.assertIn("architect, product-manager", prompts[0])
            self.assertIn(str(project_dir / ".claude" / "settings.json"), prompts[0])

    def test_cleanup_mcp_is_noop(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tmp_path = Path(td)
            feature_dir = tmp_path / "feature"
            project_dir = tmp_path / "project"
            feature_dir.mkdir()
            project_dir.mkdir()

            cleanup_mcp(feature_dir, project_dir)

            self.assertTrue(feature_dir.exists())
            self.assertTrue(project_dir.exists())


if __name__ == "__main__":
    unittest.main()
