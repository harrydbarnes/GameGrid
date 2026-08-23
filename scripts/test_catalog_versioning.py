#!/usr/bin/env python3
"""Public contract tests for versioned GameGrid catalogue artefacts."""
import unittest
from pathlib import Path

import build_catalog_v3 as catalog

ROOT = Path(__file__).resolve().parents[1]


class CatalogueVersioningTests(unittest.TestCase):
    def test_reset_schedule_starts_today_and_numbers_each_mode_from_one(self):
        self.assertEqual(catalog.START.isoformat(), '2026-08-23')
        source = (ROOT / 'scripts' / 'build_catalog_v3.py').read_text(encoding='utf-8')
        # The counter is deliberately initialised inside the mode loop.
        self.assertIn("d=START;mode_ps=[];pid=1", source)

    def test_duplicate_per_mode_ids_are_always_looked_up_with_the_mode(self):
        app = (ROOT / 'app.js').read_text(encoding='utf-8')
        self.assertIn("p.id==b.dataset.id&&p.mode===b.dataset.mode", app)
        self.assertIn('data-mode="${p.mode}"', app)
        names = (ROOT / 'grid-names.js').read_text(encoding='utf-8')
        self.assertIn("Modern:'ModernGrid'", names)
        self.assertIn("Classic:'GameGrid'", names)

    def test_published_puzzles_replace_regenerated_dates_through_today(self):
        generated = [
            {'id': 1, 'mode': 'Classic', 'date': '2026-08-23', 'rows': ['new']},
            {'id': 2, 'mode': 'Classic', 'date': '2026-08-24', 'rows': ['new-future']},
        ]
        published = [
            {'id': 1, 'mode': 'Classic', 'date': '2026-08-23', 'rows': ['published']},
            {'id': 9, 'mode': 'Retro', 'date': '2026-08-22', 'rows': ['retained-mode']},
        ]
        merged, count = catalog.preserve_published_puzzles(
            generated, published, catalog.dt.date(2026, 8, 23)
        )
        by_key = {(p['mode'], p['date']): p for p in merged}
        self.assertEqual(count, 2)
        self.assertEqual(by_key[('Classic', '2026-08-23')]['rows'], ['published'])
        self.assertEqual(by_key[('Classic', '2026-08-24')]['rows'], ['new-future'])
        self.assertIn(('Retro', '2026-08-22'), by_key)

    def test_catalogue_hash_is_stable_and_changes_with_catalogue_content(self):
        clues = [{'id': 'action', 'kind': 'genre', 'value': 'action'}]
        games = [{'id': '1', 'title': 'Example', 'year': 2000}]
        self.assertEqual(catalog.catalogue_hash(games, clues), catalog.catalogue_hash(games, clues))
        self.assertNotEqual(
            catalog.catalogue_hash(games, clues),
            catalog.catalogue_hash([{**games[0], 'year': 2001}], clues),
        )

    def test_every_puzzle_is_stamped_with_catalogue_and_build_hashes(self):
        puzzles = [{'id': 1, 'mode': 'Classic'}]
        catalog_hash, build_hash = catalog.version_puzzles(puzzles, 'catalogue-test')
        self.assertEqual(catalog_hash, 'catalogue-test')
        self.assertEqual(puzzles[0]['catalogHash'], 'catalogue-test')
        self.assertEqual(puzzles[0]['buildHash'], build_hash)
        self.assertRegex(build_hash, r'^[0-9a-f]{16}$')

    def test_catalogue_assets_split_puzzles_index_search_and_details(self):
        assets = catalog.catalogue_assets('0123456789abcdef')
        self.assertEqual(assets['dataAsset'], 'puzzle.0123456789abcdef.js')
        self.assertEqual(assets['indexAsset'], 'index.0123456789abcdef.js')
        self.assertEqual(assets['searchAsset'], 'search.0123456789abcdef.js')
        self.assertEqual(assets['detailsAsset'], 'details.0123456789abcdef.js')

    def test_details_filename_is_based_on_final_asset_bytes(self):
        first = 'window.GAMEGRID_DETAILS={"games":{}};\n'
        second = 'window.GAMEGRID_DETAILS={"games":{"1":{"coverUrl":"cover"}}};\n'
        self.assertEqual(
            catalog.details_asset_name(first),
            f'details.{catalog.content_fingerprint(first)}.js',
        )
        self.assertNotEqual(catalog.details_asset_name(first), catalog.details_asset_name(second))

    def test_search_worker_imports_the_fingerprinted_index(self):
        worker = catalog.search_worker('index.0123456789abcdef.js')
        self.assertIn("const INDEX_ASSET=\"./index.0123456789abcdef.js\"", worker)
        self.assertIn('importScripts(INDEX_ASSET)', worker)
        self.assertIn("type:'results'", worker)

    def test_search_order_is_neutral_after_relevance(self):
        worker = catalog.search_worker('index.0123456789abcdef.js')
        self.assertIn('function titleOrder', worker)
        self.assertIn('titleOrder(a.row,b.row)', worker)
        self.assertIn('list.sort(titleOrder)', worker)
        self.assertNotIn('popularity(row)', worker)

        app = (ROOT / 'app.js').read_text(encoding='utf-8')
        self.assertIn('function titleOrder', app)
        self.assertIn('titleOrder(a.g,b.g)', app)
        self.assertIn('list.slice().sort(titleOrder)', app)
        self.assertNotIn('searchScore(g,query)+popularity(g)', app)

    def test_pair_sets_are_translated_from_positions_to_game_ids(self):
        games = [{'id': 'first'}, {'id': 'second'}]
        pair_sets = {('col', 'row'): {1}}
        self.assertEqual(catalog.game_ids_for_pair(games, pair_sets, 'row', 'col'), {'second'})

    def test_asset_sizes_report_and_budget_gate(self):
        sizes = {
            'dataAsset': {'file': 'puzzle.js', 'bytes': 100, 'gzipBytes': 50},
            'indexAsset': {'file': 'index.js', 'bytes': 200, 'gzipBytes': 80},
            'searchAsset': {'file': 'search.js', 'bytes': 10, 'gzipBytes': 10},
            'detailsAsset': {'file': 'details.js', 'bytes': 300, 'gzipBytes': 100},
            'puzzleIndex': {
                'bytes': 300,
                'gzipBytes': 130,
                'assets': ['dataAsset', 'indexAsset'],
            },
        }
        self.assertEqual(sizes['puzzleIndex']['bytes'], sizes['dataAsset']['bytes'] + sizes['indexAsset']['bytes'])
        self.assertEqual(catalog.performance_budget_errors(sizes), [])
        oversized = dict(sizes)
        oversized['puzzleIndex'] = {'bytes': catalog.PERFORMANCE_BUDGETS['puzzleIndexBytes'] + 1, 'gzipBytes': 0}
        self.assertTrue(catalog.performance_budget_errors(oversized))


if __name__ == '__main__':
    unittest.main()
