#!/usr/bin/env python3
"""Public rules for GameGrid puzzle composition and difficulty."""
import unittest

import build_catalog_v3 as puzzles


def clue(identifier, kind):
    return {'id': identifier, 'kind': kind, 'value': identifier}


class PuzzleRuleTests(unittest.TestCase):
    def test_difficulty_is_set_by_the_smallest_cell_pool(self):
        self.assertEqual(puzzles.difficulty_for([20, 25, 44]), 'Easy')
        self.assertEqual(puzzles.difficulty_for([8, 30, 90]), 'Medium')
        self.assertEqual(puzzles.difficulty_for([3, 40, 100]), 'Hard')

    def test_balanced_grid_has_every_core_knowledge_family(self):
        criteria = [
            clue('ps5', 'platform'), clue('adventure', 'genre'),
            clue('y2020s', 'yearRange'), clue('rating85', 'rating'),
            clue('oneword', 'titleWords'), clue('lettera', 'titleInitial'),
        ]
        self.assertTrue(puzzles.balanced_families(criteria))

    def test_title_initials_are_limited_to_one_per_grid(self):
        criteria = [
            clue('ps5', 'platform'), clue('adventure', 'genre'),
            clue('y2020s', 'yearRange'), clue('rating85', 'rating'),
            clue('lettera', 'titleInitial'), clue('letterg', 'titleInitial'),
        ]
        self.assertFalse(puzzles.balanced_families(criteria))


if __name__ == '__main__':
    unittest.main()
