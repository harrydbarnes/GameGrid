#!/usr/bin/env python3
"""Contract tests for catalogue metadata quality gates."""
import unittest

import catalog_quality as quality


def game(title='Example', year=2020, platforms=None, tags=None, rating=80):
    return {
        'title': title,
        'year': year,
        'platforms': platforms or ['PC'],
        'tags': tags or ['Adventure'],
        'rating': rating,
    }


class CatalogueQualityTests(unittest.TestCase):
    def test_playable_pool_requires_complete_metadata_and_participation(self):
        strong = game('Strong', rating=82)
        strong['ratingsCount'] = 2
        no_signal = game('No signal', rating=82)
        no_signal['ratingsCount'] = 1
        no_genre = game('No genre', rating=82)
        no_genre['ratingsCount'] = 50
        no_genre['tags'] = []
        no_rating = game('No rating', rating=0)
        no_rating['ratingsCount'] = 50

        playable = quality.playable_games([strong, no_signal, no_genre, no_rating])

        self.assertEqual(playable, [strong])
        self.assertGreater(quality.playability_score(strong), quality.playability_score(no_signal))

    def test_metadata_coverage_reports_each_usable_field(self):
        games = [game(), game(title='Other', year=2021, rating=0)]
        coverage = quality.metadata_coverage(games)
        self.assertEqual(coverage['title']['present'], 2)
        self.assertEqual(coverage['year']['present'], 2)
        self.assertEqual(coverage['platform']['present'], 2)
        self.assertEqual(coverage['genre']['present'], 2)
        self.assertEqual(coverage['rating']['present'], 1)
        self.assertEqual(coverage['rating']['coverage'], 0.5)

    def test_metadata_quality_rejects_collapsed_genres_and_ratings(self):
        games = [game(rating=0) for _ in range(20)]
        for item in games:
            item['tags'] = []
        errors = quality.metadata_quality_errors(games)
        self.assertTrue(any('genre coverage' in error for error in errors))
        self.assertTrue(any('rating coverage' in error for error in errors))

    def test_platform_landmarks_require_bioshock_on_xbox_and_every_target_platform(self):
        games = [
            game('BioShock', platforms=['PC']),
            game('The Legend of Zelda: Breath of the Wild', platforms=['Switch']),
            game('Astro Bot', platforms=['PlayStation 5']),
            game('Alan Wake 2', platforms=['Xbox Series']),
            game('Resident Evil 4', platforms=['PC']),
        ]
        errors = quality.platform_landmark_errors(games)
        self.assertIn('BioShock is not mapped to an Xbox platform', errors)
        self.assertIn('Resident Evil 4 is not mapped to GameCube', errors)
        self.assertFalse(any('Switch' in error for error in errors))
        self.assertFalse(any('PlayStation 5' in error for error in errors))
        self.assertFalse(any('Xbox Series' in error for error in errors))

    def test_platform_landmarks_consider_every_release_with_the_same_title(self):
        games = [
            game('BioShock', platforms=['PlayStation 3']),
            game('BioShock', platforms=['Xbox 360']),
            game('Resident Evil 4', platforms=['PC']),
            game('Resident Evil 4', platforms=['GameCube']),
            game('The Legend of Zelda: Breath of the Wild', platforms=['Switch']),
            game('Astro Bot', platforms=['PlayStation 5']),
            game('Alan Wake 2', platforms=['Xbox Series']),
        ]
        self.assertEqual(quality.platform_landmark_errors(games), [])


if __name__ == '__main__':
    unittest.main()
