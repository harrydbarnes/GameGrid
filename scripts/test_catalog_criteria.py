#!/usr/bin/env python3
"""Public matching rules for supported catalogue criteria."""
import unittest

import build_catalog as catalog
import build_catalog_v3 as catalog_v3


class CatalogueCriteriaTests(unittest.TestCase):
    def test_console_generation_matches_any_platform_in_that_generation(self):
        sixth = {'kind': 'platformAny', 'value': ['PlayStation 2', 'GameCube', 'Xbox']}
        self.assertTrue(catalog.match({'platforms': ['GameCube']}, sixth))
        self.assertFalse(catalog.match({'platforms': ['PlayStation 5']}, sixth))

    def test_original_release_era_cannot_precede_console_generation(self):
        nineties = {'id': 'y1990s', 'kind': 'yearRange', 'value': [1990, 1999]}
        gen9 = {'id': 'gen9', 'kind': 'platformAny', 'value': ['PlayStation 5', 'Xbox Series', 'Switch 2']}
        self.assertFalse(catalog_v3.criteria_are_temporally_compatible(nineties, gen9))
        self.assertFalse(catalog_v3.criteria_are_temporally_compatible(gen9, nineties))

    def test_current_era_can_pair_with_console_generation(self):
        twenties = {'id': 'y2020s', 'kind': 'yearRange', 'value': [2020, 2029]}
        gen9 = {'id': 'gen9', 'kind': 'platformAny', 'value': ['PlayStation 5', 'Xbox Series', 'Switch 2']}
        self.assertTrue(catalog_v3.criteria_are_temporally_compatible(twenties, gen9))


if __name__ == '__main__':
    unittest.main()
