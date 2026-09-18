import importlib.util
import hashlib
import json
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "profile_generator", ROOT / "scripts" / "generate_profile.py"
)
GENERATOR = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(GENERATOR)


class ProfileGeneratorTests(unittest.TestCase):
    def test_config_has_four_positioned_projects(self):
        config = GENERATOR.load_config(ROOT / "profile.json")
        self.assertEqual(len(config["projects"]), 4)
        positions = {project["position"] for project in config["projects"]}
        self.assertEqual(positions, set(GENERATOR.PROJECT_POSITIONS))

    def test_safe_escapes_svg_text(self):
        self.assertEqual(
            GENERATOR.safe('<script data-x="1">&'),
            "&lt;script data-x=&quot;1&quot;&gt;&amp;",
        )

    def test_offline_generation_produces_valid_themes(self):
        with tempfile.TemporaryDirectory() as temporary:
            outputs = GENERATOR.generate(
                ROOT / "profile.json", Path(temporary), offline=True
            )
            self.assertEqual(
                {path.name for path in outputs},
                {
                    "profile-data.json",
                    "profile-dark.svg",
                    "profile-light.svg",
                    "profile-dark-mobile.svg",
                    "profile-light-mobile.svg",
                },
            )
            for path in outputs:
                if path.suffix == ".json":
                    data = json.loads(path.read_text(encoding="utf-8"))
                    self.assertEqual(data["public"]["public_repos"], 17)
                    self.assertEqual(len(data["projects"]), 4)
                    continue
                root = ET.parse(path).getroot()
                expected_viewbox = (
                    "0 0 720 960" if "mobile" in path.name else "0 0 1200 640"
                )
                self.assertEqual(root.attrib["viewBox"], expected_viewbox)
                content = path.read_text(encoding="utf-8")
                self.assertIn("KTM-NP-0545", content)
                self.assertIn("prefers-reduced-motion", content)
                self.assertIn("UPDATED", content)
                self.assertIn("PROJECT TRANSMISSION", content)
                self.assertNotIn("None", content)

    def test_offline_generation_is_deterministic(self):
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            first_outputs = GENERATOR.generate(
                ROOT / "profile.json", Path(first), offline=True
            )
            second_outputs = GENERATOR.generate(
                ROOT / "profile.json", Path(second), offline=True
            )
            first_content = {
                path.name: path.read_bytes() for path in first_outputs
            }
            second_content = {
                path.name: path.read_bytes() for path in second_outputs
            }
            self.assertEqual(first_content, second_content)

    def test_offline_artwork_matches_reviewed_snapshots(self):
        expected = json.loads(
            (ROOT / "tests" / "profile_snapshots.json").read_text(encoding="utf-8")
        )
        with tempfile.TemporaryDirectory() as temporary:
            outputs = GENERATOR.generate(
                ROOT / "profile.json", Path(temporary), offline=True
            )
            actual = {
                path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                for path in outputs
            }
        self.assertEqual(actual, expected)

    def test_fallback_includes_selected_repository_signals(self):
        config = GENERATOR.load_config(ROOT / "profile.json")
        telemetry = GENERATOR.fetch_telemetry(config, offline=True)
        self.assertEqual(
            set(telemetry["projects"]),
            {project["repo"] for project in config["projects"]},
        )

    def test_invalid_project_count_is_rejected(self):
        config = json.loads((ROOT / "profile.json").read_text(encoding="utf-8"))
        config["projects"] = config["projects"][:3]
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "invalid.json"
            path.write_text(json.dumps(config), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "exactly four"):
                GENERATOR.load_config(path)


if __name__ == "__main__":
    unittest.main()
