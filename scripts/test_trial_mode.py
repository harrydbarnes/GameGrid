#!/usr/bin/env python3
"""Contract tests for the maker-by-context Trial mode."""
import random
import unittest

import build_catalog as catalog
import build_catalog_v2 as modes
import build_catalog_v3 as puzzles


def sample_games():
    games=[]
    for index in range(60):
        games.append({
            'id':str(index),
            'title':f'Game {index}',
            'year':2000+index%20,
            'platforms':['PC','PlayStation 5'],
            'tags':['adventure','rpg'],
            'rating':85,
            'ratingsCount':100,
            'developers':[f'Studio {index%3}'],
            'publishers':[f'Publisher {index%2}'],
            'franchise':f'Series {index%4}',
        })
    return games


class TrialModeTests(unittest.TestCase):
    def test_trial_is_a_scheduled_mode(self):
        self.assertIn('Trial', modes.MODES)

    def test_trial_specs_are_maker_criteria_with_meaningful_pools(self):
        specs=catalog.trial_specs(sample_games(), min_games=3)
        self.assertTrue(specs)
        self.assertTrue(all(spec['kind'] in {'developer','publisher','publisherFamily','franchise'} for spec in specs))
        self.assertTrue(all(spec['id'].split(':',1)[0]==spec['kind'] for spec in specs))

    def test_publisher_family_alias_is_matchable(self):
        game={'id':'bethesda','publishers':['Bethesda Softworks'],'developers':[],'franchise':''}
        specs=catalog.trial_specs([game],min_games=1)
        family=next(spec for spec in specs if spec['kind']=='publisherFamily')
        self.assertEqual(family['value'],'Xbox / Microsoft')
        self.assertTrue(catalog.match(game,family))

    def test_trial_grid_has_maker_rows_and_varied_context_columns(self):
        games=sample_games()
        specs=modes.specs_for_mode(games,'Trial')
        scoped,counts,pool,pairs=modes.build_index(games,'Trial',specs)
        selected=puzzles.trial_six(puzzles.trial_buckets(pool),{'maker':0,**{family:0 for family in puzzles.CORE_FAMILIES}},random.Random(7))
        self.assertIsNotNone(selected)
        self.assertEqual(sum(puzzles.clue_family(spec)=='maker' for spec in selected),3)
        self.assertTrue(puzzles.balanced_families(selected))
        self.assertGreaterEqual(len(set(puzzles.clue_family(spec) for spec in selected if puzzles.clue_family(spec)!='maker')),2)
        self.assertTrue(scoped)
        self.assertTrue(pairs)
        self.assertTrue(all(not (key[0].split(':',1)[0] in {'developer','publisher','franchise'} and key[1].split(':',1)[0] in {'developer','publisher','franchise'}) for key in pairs))

    def test_trial_puzzle_keeps_makers_on_left_axis(self):
        games=sample_games()
        specs=modes.specs_for_mode(games,'Trial')
        scoped,counts,pool,pairs=modes.build_index(games,'Trial',specs)
        puzzle=puzzles.make_puzzle('Trial',catalog.START,1,[],pool,pairs,random.Random(11),len(scoped),{'maker':0,**{family:0 for family in puzzles.CORE_FAMILIES}})
        by_id={spec['id']:spec for spec in pool}
        self.assertTrue(all(puzzles.clue_family(by_id[criterion])=='maker' for criterion in puzzle['rows']))
        self.assertTrue(all(puzzles.clue_family(by_id[criterion])!='maker' for criterion in puzzle['cols']))

    def test_puzzle_bootstrap_keeps_maker_metadata(self):
        row=puzzles.compact_puzzle_index(sample_games()[:1])[0]
        self.assertEqual(row[7], ['Studio 0'])
        self.assertEqual(row[8], ['Publisher 0'])
        self.assertEqual(row[9], 'Series 0')


if __name__=='__main__':
    unittest.main()
