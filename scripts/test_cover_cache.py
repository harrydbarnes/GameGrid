#!/usr/bin/env python3
"""Contract tests for the persistent IGDB cover lookup cache."""
import json
import unittest
from pathlib import Path

try:
    from enrich_covers import load_cover_cache, missing_cover_ids, save_cover_cache
except SystemExit as error:
    raise AssertionError('enrich_covers.py must expose cache helpers without running enrichment on import') from error


class CoverCacheTests(unittest.TestCase):
    def test_cache_round_trip_and_only_new_ids_are_missing(self):
        path = Path(__file__).resolve().parents[1] / 'cover-cache-test.json'
        try:
            save_cover_cache(path, 'catalogue-a', {'1': 'image-1'}, {'1', '2'})
            cache = load_cover_cache(path)
            self.assertEqual(cache['catalogHash'], 'catalogue-a')
            self.assertEqual(missing_cover_ids([1, 2, 3], cache), [3])
        finally:
            path.unlink(missing_ok=True)

    def test_invalid_cache_is_ignored(self):
        path = Path(__file__).resolve().parents[1] / 'cover-cache-test.json'
        try:
            path.write_text(json.dumps({'version': 999, 'covers': {'1': 'old'}}), encoding='utf-8')
            cache = load_cover_cache(path)
            self.assertEqual(cache['covers'], {})
            self.assertEqual(missing_cover_ids([1], cache), [1])
        finally:
            path.unlink(missing_ok=True)


if __name__ == '__main__':
    unittest.main()
