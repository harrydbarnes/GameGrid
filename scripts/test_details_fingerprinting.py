"""Regression tests for the final, cover-enriched details asset fingerprint."""
import json
import unittest
from pathlib import Path

from enrich_covers import details_asset_name, finalize_details_asset


ROOT = Path(__file__).resolve().parents[1]


class DetailsFingerprintingTests(unittest.TestCase):
    def test_cover_changes_produce_a_different_details_filename(self):
        without_cover = 'window.GAMEGRID_DETAILS=' + json.dumps({
            'catalogHash': 'catalogue-a',
            'buildHash': 'build-a',
            'games': {'1': {'developers': ['Example']}},
        }, separators=(',', ':')) + ';\n'
        with_cover = without_cover.replace(
            '"developers":["Example"]',
            '"developers":["Example"],"coverUrl":"https://images.example/cover.jpg"',
        )
        self.assertNotEqual(details_asset_name(without_cover), details_asset_name(with_cover))

    def test_finalizer_updates_manifest_and_puzzle_pointer(self):
        manifest_path = ROOT / 'details-fingerprint-test-manifest.js'
        data_path = ROOT / 'puzzle.1111111111111111.js'
        old_details_path = ROOT / 'details.2222222222222222.js'
        report_path = ROOT / 'details-fingerprint-test-report.json'
        final_text = 'window.GAMEGRID_DETAILS={"catalogHash":"catalogue-a","buildHash":"build-a","games":{}};\n'
        final_asset = details_asset_name(final_text)
        assets = {
            'dataAsset': data_path.name,
            'indexAsset': 'index.1111111111111111.js',
            'searchAsset': 'search.1111111111111111.js',
            'detailsAsset': old_details_path.name,
        }
        try:
            data_path.write_text(
                'return {meta:{"detailsAsset":"' + old_details_path.name + '"}};',
                encoding='utf-8',
            )
            old_details_path.write_text('old details', encoding='utf-8')
            manifest_path.write_text(
                'window.GAMEGRID_CATALOG_MANIFEST=' + json.dumps(assets, separators=(',', ':')) + ';\n',
                encoding='utf-8',
            )
            report_path.write_text('{}', encoding='utf-8')

            final_asset = finalize_details_asset(
                final_text,
                assets,
                root=ROOT,
                manifest_path=manifest_path,
            )

            self.assertEqual(final_asset, details_asset_name(final_text))
            self.assertNotEqual(final_asset, old_details_path.name)
            self.assertTrue((ROOT / final_asset).exists())
            self.assertFalse(old_details_path.exists())
            self.assertIn(final_asset, data_path.read_text(encoding='utf-8'))
            manifest = json.loads(
                manifest_path.read_text(encoding='utf-8').split('=', 1)[1].rstrip(';\n'),
            )
            self.assertEqual(manifest['detailsAsset'], final_asset)
            self.assertEqual(manifest['detailsHash'], final_asset.removeprefix('details.').removesuffix('.js'))
        finally:
            manifest_path.unlink(missing_ok=True)
            report_path.unlink(missing_ok=True)
            data_path.unlink(missing_ok=True)
            old_details_path.unlink(missing_ok=True)
            (ROOT / final_asset).unlink(missing_ok=True)


if __name__ == '__main__':
    unittest.main()
