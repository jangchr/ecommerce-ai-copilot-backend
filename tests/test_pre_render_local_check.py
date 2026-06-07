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
