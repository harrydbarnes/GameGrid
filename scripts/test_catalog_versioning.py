#!/usr/bin/env python3
"""Public contract tests for versioned GameGrid catalogue artefacts."""
import unittest

import build_catalog_v3 as catalog


class CatalogueVersioningTests(unittest.TestCase):
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

    def test_search_worker_imports_the_fingerprinted_index(self):
        worker = catalog.search_worker('index.0123456789abcdef.js')
        self.assertIn("const INDEX_ASSET=\"./index.0123456789abcdef.js\"", worker)
        self.assertIn('importScripts(INDEX_ASSET)', worker)
        self.assertIn("type:'results'", worker)

    def test_pair_sets_are_translated_from_positions_to_game_ids(self):
        games = [{'id': 'first'}, {'id': 'second'}]
        pair_sets = {('row', 'col'): {1}}
        self.assertEqual(catalog.game_ids_for_pair(games, pair_sets, 'row', 'col'), {'second'})


if __name__ == '__main__':
    unittest.main()
