import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "pre_render_local_check.ps1"


class PreRenderLocalCheckScriptTests(unittest.TestCase):
    def test_pre_render_local_check_script_exists(self):
        self.assertTrue(SCRIPT.exists())

    def test_pre_render_local_check_contains_required_steps(self):
        text = SCRIPT.read_text(encoding="utf-8")
        for marker in [
            "Pre-render local readiness bundle",
            "frontend_quality_guard.py",
            "scripts\\cg.ps1",
            "scripts\\run_all_tests.py",
            "Run frontend quality guard",
            "Run cg gate",
            "Run fast regression suite",
            "Fast suite skipped",
            "render_deploy_required: false",
            "Pre-render local readiness PASS.",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, text)

    def test_pre_render_local_check_json_only(self):
        result = subprocess.run(
            [
                "powershell",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(SCRIPT),
                "-JsonOnly",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("Pre-render local readiness bundle", result.stdout)
        self.assertIn("latest_commit", result.stdout)
        self.assertIn("render_deploy_required", result.stdout)

class CgRunnerPreRenderCommandTests(unittest.TestCase):
    def test_cg_runner_has_pre_render_commands(self):
        text = (ROOT / "scripts" / "cg.ps1").read_text(encoding="utf-8")
        for marker in [
            "function PreRender([bool]$RunFastSuite = $false)",
            '"pre-render" { PreRender $false }',
            '"pre-render-fast" { PreRender $true }',
            ".\\scripts\\cg.ps1 pre-render",
            ".\\scripts\\cg.ps1 pre-render-fast",
            "Run frontend quality guard",
            "Run fast regression suite",
            "Fast suite skipped. Run .\\scripts\\cg.ps1 pre-render-fast before a real Render batch.",
            "Pre-render local readiness bundle",
            "render_deploy_required: false",
            "Pre-render local readiness PASS.",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, text)

    def test_cg_runner_help_lists_pre_render_commands(self):
        result = subprocess.run(
            [
                "powershell",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(ROOT / "scripts" / "cg.ps1"),
                "help",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn(".\\scripts\\cg.ps1 pre-render", result.stdout)
        self.assertIn(".\\scripts\\cg.ps1 pre-render-fast", result.stdout)


class CgRunnerBatchGateCommandTests(unittest.TestCase):
    def test_cg_runner_has_batch_gate_command(self):
        text = (ROOT / "scripts" / "cg.ps1").read_text(encoding="utf-8")
        for marker in [
            "function BatchGate()",
            '"batch-gate" { BatchGate }',
            ".\\scripts\\cg.ps1 batch-gate",
            "Run super-batch frontend quality guard",
            "Run super-batch focused unit tests",
            "tests.test_agent_runs",
            "tests.test_supervisor_planner",
            "tests.test_frontend_probe_boundary",
            "tests.test_frontend_quality_guard",
            "tests.test_pre_render_local_check",
            "Fast suite intentionally skipped for local super-batch; run .\\scripts\\cg.ps1 pre-render-fast before Render.",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, text)

    def test_cg_runner_help_lists_batch_gate_command(self):
        result = subprocess.run(
            [
                "powershell",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(ROOT / "scripts" / "cg.ps1"),
                "help",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn(".\\scripts\\cg.ps1 batch-gate", result.stdout)
