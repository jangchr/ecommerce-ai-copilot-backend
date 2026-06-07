import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "frontend_quality_guard.py"


class FrontendQualityGuardScriptTests(unittest.TestCase):
    def test_frontend_quality_guard_script_exists(self):
        self.assertTrue(SCRIPT.exists())

    def test_frontend_quality_guard_json_passes(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--json"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["ok"], payload)
        self.assertIn("static/index.html", payload["checked_files"])
        self.assertIn("scripts/smoke_agent_graph_os_public.ps1", payload["checked_files"])
        self.assertGreaterEqual(payload["html_marker_count"], 8)
        self.assertGreaterEqual(payload["smoke_marker_count"], 8)
        self.assertEqual(payload["issues"], [])

    def test_frontend_quality_guard_human_output_passes(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("CrossGrowth frontend quality guard", result.stdout)
        self.assertIn("OK: True", result.stdout)
