#!/usr/bin/env python3
"""Regression checks for the public era-mode boundaries."""
import unittest

import build_catalog_v2 as modes


def game(year):
    return {'year': year, 'platforms': []}


class EraModeScopeTests(unittest.TestCase):
    def test_retro_ends_before_the_ps2_era(self):
        self.assertTrue(modes.scope_ok(game(1999), 'Retro'))
        self.assertFalse(modes.scope_ok(game(2000), 'Retro'))

    def test_modern_begins_with_the_ps2_era(self):
        self.assertFalse(modes.scope_ok(game(1999), 'Modern'))
        self.assertTrue(modes.scope_ok(game(2000), 'Modern'))

    def test_modern_is_a_scheduled_mode(self):
        self.assertIn('Modern', modes.MODES)


if __name__ == '__main__':
    unittest.main()
