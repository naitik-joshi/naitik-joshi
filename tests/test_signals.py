import importlib.util
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "signal_renderer", ROOT / "scripts" / "render_signals.py"
)
SIGNALS = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(SIGNALS)


class SignalRendererTests(unittest.TestCase):
    def test_extracts_issue_form_signal(self):
        body = "### Signal\nBuilt something useful today.\n\n### Public display\n- [x] Yes"
        self.assertEqual(
            SIGNALS.extract_signal(body, "[profile-signal] fallback"),
            "Built something useful today.",
        )

    def test_signal_text_is_svg_escaped(self):
        rendered = SIGNALS.render_signals(
            [{"author": "dev", "message": "ship <script> & learn", "url": ""}],
            "dark",
        )
        ET.fromstring(rendered)
        self.assertIn("ship &lt;script&gt; &amp; learn", rendered)

    def test_allowlist_rejects_non_integer_values(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "signals.json"
            path.write_text('{"approved_issue_numbers": ["7"]}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "list of issue numbers"):
                SIGNALS.load_allowlist(path)


if __name__ == "__main__":
    unittest.main()
