#!/usr/bin/env python3
"""Public matching rules for supported catalogue criteria."""
import unittest

import build_catalog as catalog
import build_catalog_v3 as catalog_v3


class CatalogueCriteriaTests(unittest.TestCase):
    def test_unix_timestamps_are_converted_before_year_substrings(self):
        self.assertEqual(catalog.year_of('1640995200'), 2022)
        self.assertEqual(catalog.year_of('1640995200000'), 2022)
        self.assertEqual(catalog.year_of('2020-01-01'), 2020)

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

    def test_nested_era_and_rating_clues_are_redundant(self):
        nineties = {'id': 'y1990s', 'kind': 'yearRange', 'value': [1990, 1999]}
        pre2000 = {'id': 'pre2000', 'kind': 'yearRange', 'value': [0, 1999]}
        rating80 = {'id': 'rating80', 'kind': 'rating', 'value': 75}
        rating85 = {'id': 'rating85', 'kind': 'rating', 'value': 80}
        self.assertTrue(catalog_v3.criteria_are_redundant(nineties, pre2000))
        self.assertTrue(catalog_v3.criteria_are_redundant(rating80, rating85))

    def test_platform_family_and_generation_member_are_redundant(self):
        playstation = {'id': 'playstation', 'kind': 'platform', 'value': 'PlayStation'}
        ps5 = {'id': 'ps5', 'kind': 'platform', 'value': 'PlayStation 5'}
        gen8 = {'id': 'gen8', 'kind': 'platformAny', 'value': ['PlayStation 4', 'Xbox One', 'Wii U', 'Switch']}
        switch = {'id': 'switch', 'kind': 'platform', 'value': 'Switch'}
        self.assertTrue(catalog_v3.criteria_are_redundant(playstation, ps5))
        self.assertTrue(catalog_v3.criteria_are_redundant(gen8, switch))

    def test_trial_publisher_alias_keeps_last_of_us_part_ii_playable(self):
        game = {'id': '26192', 'title': 'The Last of Us Part II', 'publishers': [], 'platforms': ['PlayStation 4']}
        self.assertEqual(catalog.known_publisher_aliases(game), ['Sony Interactive Entertainment'])
        source = catalog.js_clues([{
            'id': 'publisherFamily:sony',
            'label': 'Published by Sony',
            'kind': 'publisherFamily',
            'value': 'Sony',
        }])
        self.assertIn('g.publisherAliases', source)
        self.assertEqual(
            catalog_v3.detail_index([game])['26192']['publishers'],
            ['Sony Interactive Entertainment'],
        )

    def test_reviewed_first_party_aliases_are_used_by_the_canonical_matcher(self):
        cases = [
            ('God of War', 2018, 'Sony'),
            ('God of War Ragnarök', 2022, 'Sony'),
            ('Horizon Zero Dawn', 2017, 'Sony'),
            ('Bloodborne', 2015, 'Sony'),
            ("Uncharted 4: A Thief's End", 2016, 'Sony'),
            ('Animal Crossing: New Horizons', 2020, 'Nintendo'),
            ('Super Mario Odyssey', 2017, 'Nintendo'),
            ('Halo Infinite', 2021, 'Xbox / Microsoft'),
            ('Starfield', 2023, 'Xbox / Microsoft'),
        ]
        for title, year, family in cases:
            game = {'id': title, 'title': title, 'year': year, 'publishers': []}
            criterion = {'kind': 'publisherFamily', 'value': family}
            self.assertTrue(catalog.known_publisher_aliases(game), title)
            self.assertTrue(catalog.match(game, criterion), title)

    def test_year_specific_publisher_aliases_do_not_bleed_into_other_releases(self):
        for title, year in [('Doom', 1993), ('Prey', 2006), ('Killer Instinct', 1994)]:
            game = {'id': title, 'title': title, 'year': year, 'publishers': []}
            self.assertEqual(catalog.known_publisher_aliases(game), [])


if __name__ == '__main__':
    unittest.main()
