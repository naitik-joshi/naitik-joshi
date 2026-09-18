import hashlib
import importlib.util
import re
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "nightshift", ROOT / "scripts" / "generate_nightshift.py"
)
NIGHTSHIFT = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(NIGHTSHIFT)


class NightshiftTests(unittest.TestCase):
    def setUp(self):
        self.level, self.spawn, self.uplink = NIGHTSHIFT.load_map(
            ROOT / "game" / "map.txt"
        )

    def test_uplink_is_reachable(self):
        path = NIGHTSHIFT.shortest_path(self.level, self.spawn, self.uplink)
        self.assertEqual(path[0], self.spawn)
        self.assertEqual(path[-1], self.uplink)
        self.assertEqual(len(path) - 1, 46)

    def test_blocked_movement_stays_in_place(self):
        links = NIGHTSHIFT.linked_state(self.level, 1, 1, 3)
        self.assertEqual(links["forward"], (1, 1, 3))

    def test_compiler_builds_complete_link_graph(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            manifest = NIGHTSHIFT.generate(ROOT / "game" / "map.txt", output)
            self.assertEqual(manifest["state_count"], 284)
            self.assertEqual(len(list((output / "frames").glob("*.svg"))), 284)
            self.assertEqual(len(list((output / "play").glob("*.md"))), 284)
            for page in (output / "play").glob("*.md"):
                content = page.read_text(encoding="utf-8")
                for href in re.findall(r'href="([^"]+)"', content):
                    if re.fullmatch(r"\./x\d{2}-y\d{2}-[ESWN]\.md", href):
                        self.assertTrue((page.parent / href).resolve().exists(), href)
                source = re.search(r'src="([^"]+)"', content)
                self.assertIsNotNone(source)
                self.assertTrue((page.parent / source.group(1)).resolve().exists())

    def test_representative_frames_are_valid_and_deterministic(self):
        samples = [(1, 1, 0), (5, 5, 2), (3, 5, 2)]
        for x, y, heading in samples:
            first = NIGHTSHIFT.render_frame(self.level, x, y, heading, self.uplink)
            second = NIGHTSHIFT.render_frame(self.level, x, y, heading, self.uplink)
            ET.fromstring(first)
            self.assertEqual(
                hashlib.sha256(first.encode()).hexdigest(),
                hashlib.sha256(second.encode()).hexdigest(),
            )
            self.assertIn("NO JS / NO SERVER", first)


if __name__ == "__main__":
    unittest.main()
