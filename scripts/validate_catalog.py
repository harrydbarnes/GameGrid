#!/usr/bin/env python3
import json,re,sys
import catalog_quality as quality
manifest_text=open('catalog-manifest.js',encoding='utf-8').read()
manifest_match=re.search(r'window\.GAMEGRID_CATALOG_MANIFEST=(\{.*\});',manifest_text)
if not manifest_match:
    print('ERROR: missing generated catalogue manifest');sys.exit(1)
manifest=json.loads(manifest_match.group(1))
asset=manifest.get('dataAsset','')
if not re.fullmatch(r'data\.[a-f0-9]{16}\.js',asset):
    print('ERROR: catalogue manifest does not reference a fingerprinted data asset');sys.exit(1)
text=open(asset,encoding='utf-8').read()
report=json.load(open('catalog-report.json'))
errors=[]
games_match=re.search(r'const games=(\[.*?\]);\nconst clueSpecs=',text,re.S)
if not games_match:
    print('ERROR: unable to read games from generated catalogue asset');sys.exit(1)
games=json.loads(games_match.group(1))
if report.get('catalogHash')!=manifest.get('catalogHash') or report.get('buildHash')!=manifest.get('buildHash') or report.get('dataAsset')!=asset:
    errors.append('catalogue report and manifest disagree')
if f'"catalogHash":"{manifest.get("catalogHash","")}"' not in text or f'"buildHash":"{manifest.get("buildHash","")}"' not in text:
    errors.append('catalogue data and manifest disagree')
if report['games']<20000:errors.append('expected at least 20,000 games; catalogue may have been truncated')
if report.get('selection')!='all eligible source records (no popularity cap)':errors.append('catalogue report does not confirm uncapped source selection')
clue_counts=report.get('clueCounts',{})
# Source game files store genre/platform IDs.  A missing lookup join leaves the
# catalogue numerically large but makes genre intersections effectively empty.
if clue_counts.get('adventure',0)<10000:errors.append('Adventure coverage is unexpectedly low; genre IDs may not have been resolved')
if clue_counts.get('xbox',0)<5000:errors.append('Xbox coverage is unexpectedly low; platform IDs may not have been resolved')
coverage=quality.metadata_coverage(games)
errors.extend(quality.metadata_quality_errors(games))
errors.extend(quality.platform_coverage_errors(games))
errors.extend(quality.platform_landmark_errors(games))
if report.get('metadataCoverage')!=coverage:
    errors.append('catalogue report metadata coverage does not match generated data')
if report.get('platformCounts')!=quality.platform_counts(games):
    errors.append('catalogue report platform counts do not match generated data')
if not 40<=report['clues']<=60:errors.append('expected 40–60 clue types')
if report['puzzles']<90:errors.append('expected at least 90 daily puzzles')
for mode in ('Classic','Retro','Modern','Nintendo','PlayStation','Xbox','Deep Cut'):
    if not report.get('modes',{}).get(mode,{}).get('puzzles'):
        errors.append(f'missing generated puzzles for {mode} mode')
if report['last']<'2026-11-30':errors.append('puzzle schedule does not span a few months')
# generator only writes puzzles after every cell has >=3 answers; verify the generated file contains answerCounts for auditability
counts=re.findall(r'"answerCounts":\[([^]]+)\]',text)
if len(counts)!=report['puzzles']:errors.append('missing puzzle validation counts')
if len(re.findall(r'"catalogHash":"'+re.escape(manifest.get('catalogHash',''))+r'"',text))!=report['puzzles']+1:
    errors.append('every puzzle must carry the catalogue hash')
if len(re.findall(r'"buildHash":"'+re.escape(manifest.get('buildHash',''))+r'"',text))!=report['puzzles']+1:
    errors.append('every puzzle must carry the build hash')
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
