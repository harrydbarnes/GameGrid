#!/usr/bin/env python3
import json,re,sys
text=open('data.js',encoding='utf-8').read()
report=json.load(open('catalog-report.json'))
errors=[]
if report['games']<20000:errors.append('expected at least 20,000 games; catalogue may have been truncated')
if report.get('selection')!='all eligible source records (no popularity cap)':errors.append('catalogue report does not confirm uncapped source selection')
clue_counts=report.get('clueCounts',{})
# Source game files store genre/platform IDs.  A missing lookup join leaves the
# catalogue numerically large but makes genre intersections effectively empty.
if clue_counts.get('adventure',0)<10000:errors.append('Adventure coverage is unexpectedly low; genre IDs may not have been resolved')
if clue_counts.get('xbox',0)<5000:errors.append('Xbox coverage is unexpectedly low; platform IDs may not have been resolved')
if not 40<=report['clues']<=60:errors.append('expected 40–60 clue types')
if report['puzzles']<90:errors.append('expected at least 90 daily puzzles')
if report['last']<'2026-11-30':errors.append('puzzle schedule does not span a few months')
# generator only writes puzzles after every cell has >=3 answers; verify the generated file contains answerCounts for auditability
counts=re.findall(r'"answerCounts":\[([^]]+)\]',text)
if len(counts)!=report['puzzles']:errors.append('missing puzzle validation counts')
for i,c in enumerate(counts,1):
    nums=[int(x) for x in c.split(',')]
    if len(nums)!=9 or min(nums)<3:errors.append(f'puzzle {i} contains a weak/impossible cell')
# A release-era smoke test.  These titles span the requested last twenty years
# and catch both a truncated source catalogue and an outdated source snapshot.
spot_checks=['Gears of War','BioShock','Mass Effect','Grand Theft Auto IV','Demon’s Souls','Red Dead Redemption','The Elder Scrolls V: Skyrim','The Last of Us','Grand Theft Auto V','The Witcher 3: Wild Hunt','The Legend of Zelda: Breath of the Wild','Red Dead Redemption 2','Death Stranding','Animal Crossing: New Horizons','Elden Ring','Baldur’s Gate 3','Alan Wake 2','Astro Bot','Clair Obscur: Expedition 33']
for title in spot_checks:
    if f'"title":"{title}"' not in text:errors.append(f'missing required catalogue spot-check: {title}')
if errors:
    print('\n'.join('ERROR: '+x for x in errors));sys.exit(1)
print(f"Validated {report['games']:,} games, {report['clues']} clues and {report['puzzles']} puzzles ({report['first']} to {report['last']}).")
