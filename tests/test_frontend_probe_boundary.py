from pathlib import Path
import unittest


FRONTEND_PATH = Path(__file__).resolve().parents[1] / "static" / "index.html"


class FrontendProbeBoundaryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = FRONTEND_PATH.read_text(encoding="utf-8")

    def test_product_frontend_does_not_read_embedded_debug_state(self):
        self.assertNotIn("data.debug", self.source)

    def test_source_probe_is_guarded_by_debug_mode(self):
        self.assertIn("postCopilot('debug-source-probe'", self.source)
        self.assertIn("async function runSourceProbe()", self.source)
        self.assertIn("if (!document.getElementById('debugMode').checked) return;", self.source)
        self.assertIn("document.getElementById('sourceProbeTools').hidden = !enabled;", self.source)


if __name__ == "__main__":
    unittest.main()
