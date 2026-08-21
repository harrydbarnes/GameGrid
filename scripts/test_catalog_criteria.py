#!/usr/bin/env python3
"""Public matching rules for supported catalogue criteria."""
import unittest

import build_catalog as catalog


class CatalogueCriteriaTests(unittest.TestCase):
    def test_console_generation_matches_any_platform_in_that_generation(self):
        sixth = {'kind': 'platformAny', 'value': ['PlayStation 2', 'GameCube', 'Xbox']}
        self.assertTrue(catalog.match({'platforms': ['GameCube']}, sixth))
        self.assertFalse(catalog.match({'platforms': ['PlayStation 5']}, sixth))


if __name__ == '__main__':
    unittest.main()
