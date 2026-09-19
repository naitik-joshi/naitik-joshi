import importlib.util
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('preview', ROOT / 'scripts/generate_patchbay_preview.py')
PREVIEW = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PREVIEW)

class PatchbayPreviewTests(unittest.TestCase):
    def test_both_assets_are_valid_and_current(self):
        for mobile in (False, True):
            source = PREVIEW.render(mobile)
            root = ET.fromstring(source)
            self.assertEqual(root.tag, '{http://www.w3.org/2000/svg}svg')
            filename = 'patchbay-preview-mobile.svg' if mobile else 'patchbay-preview.svg'
            self.assertEqual((ROOT / 'assets' / filename).read_text(), source)

    def test_script_free_and_reduced_motion(self):
        for mobile in (False, True):
            source = PREVIEW.render(mobile)
            self.assertNotIn('<script', source)
            self.assertNotIn('foreignObject', source)
            self.assertIn('prefers-reduced-motion:reduce', source)
            self.assertIn('ANIMATED PREVIEW', source)

    def test_readme_links_to_actual_tool_not_maze(self):
        readme = (ROOT / 'README.md').read_text()
        self.assertIn('https://naitik-joshi.github.io/naitik-joshi/', readme)
        self.assertIn('patchbay-preview-mobile.svg', readme)
        self.assertNotIn('./game/', readme)

if __name__ == '__main__':
    unittest.main()
