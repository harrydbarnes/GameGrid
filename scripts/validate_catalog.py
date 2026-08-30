#!/usr/bin/env python3
import json,re,sys
import catalog_quality as quality
import build_catalog_v2 as modes
import build_catalog_v3 as puzzle_rules
manifest_text=open('catalog-manifest.js',encoding='utf-8').read()
manifest_match=re.search(r'window\.GAMEGRID_CATALOG_MANIFEST=(\{.*\});',manifest_text)
if not manifest_match:
    print('ERROR: missing generated catalogue manifest');sys.exit(1)
manifest=json.loads(manifest_match.group(1))
asset=manifest.get('dataAsset','')
index_asset=manifest.get('indexAsset','')
search_asset=manifest.get('searchAsset','')
details_asset=manifest.get('detailsAsset','')
if not re.fullmatch(r'puzzle\.[a-f0-9]{16}\.js',asset) or not re.fullmatch(r'index\.[a-f0-9]{16}\.js',index_asset) or not re.fullmatch(r'search\.[a-f0-9]{16}\.js',search_asset) or not re.fullmatch(r'details\.[a-f0-9]{16}\.js',details_asset):
    print('ERROR: catalogue manifest does not reference fingerprinted split assets');sys.exit(1)
text=open(asset,encoding='utf-8').read()
index_text=open(index_asset,encoding='utf-8').read()
search_text=open(search_asset,encoding='utf-8').read()
details_text=open(details_asset,encoding='utf-8').read()
report=json.load(open('catalog-report.json'))
errors=[]
details_hash=manifest.get('detailsHash')
if not re.fullmatch(r'[a-f0-9]{16}',details_hash or ''):
    errors.append('catalogue manifest is missing the final details hash')
else:
    expected_details_hash=puzzle_rules.content_fingerprint(details_text)
    if details_hash!=expected_details_hash or details_asset!=f'details.{expected_details_hash}.js':
        errors.append('deferred details asset filename does not fingerprint its final bytes')
try:
    actual_asset_sizes=puzzle_rules.asset_sizes({
        'dataAsset':asset,
        'indexAsset':index_asset,
        'searchAsset':search_asset,
        'detailsAsset':details_asset,
    })
except (OSError,TypeError) as exc:
    actual_asset_sizes=None
    errors.append(f'unable to measure generated catalogue assets: {exc}')
if actual_asset_sizes is not None:
    if report.get('assetSizes')!=actual_asset_sizes:
        errors.append('catalogue report asset sizes do not match generated files')
    if report.get('performanceBudgets')!=puzzle_rules.PERFORMANCE_BUDGETS:
        errors.append('catalogue report performance budgets do not match CI policy')
    errors.extend(puzzle_rules.performance_budget_errors(actual_asset_sizes))
index_match=re.search(r'(?:window|globalThis)\.GAMEGRID_INDEX=(\[.*\]);',index_text,re.S)
if not index_match:
    print('ERROR: unable to read compact search index');sys.exit(1)
details_match=re.search(r'window\.GAMEGRID_DETAILS=(\{.*\});',details_text,re.S)
if not details_match:
    errors.append('unable to read deferred game-details payload')
    detail_games={}
else:
    try:
        detail_games=json.loads(details_match.group(1)).get('games',{})
    except (TypeError,ValueError):
        detail_games={}

def compact_game(row):
    return {'id':row[0],'title':row[1],'year':row[2],'platforms':row[3],'tags':row[4],'rating':row[5],'ratingsCount':row[6],
            'developers':row[7] if len(row)>7 and isinstance(row[7],list) else [],
            'publishers':row[8] if len(row)>8 and isinstance(row[8],list) else [],
            'franchise':row[9] if len(row)>9 else '',
            'publisherAliases':row[10] if len(row)>10 and isinstance(row[10],list) else []}

games=[compact_game(row) for row in json.loads(index_match.group(1))]
for game in games:
    details=detail_games.get(str(game['id'])) or detail_games.get(game['id']) or {}
    for key in ('developers','publishers','franchise'):
        if details.get(key):game[key]=details[key]
if 'importScripts(' not in search_text or f'./{index_asset}' not in search_text:
    errors.append('search worker does not import the fingerprinted compact index')
puzzle_games_match=re.search(r'const games=(\[.*?\])\.map\(\(\[id,title,year,platforms,tags,rating,ratingsCount(?:,developers,publishers,franchise,publisherAliases)?\]',text,re.S)
if not puzzle_games_match:
    errors.append('unable to read the compact puzzle bootstrap data')
    puzzle_games=[]
else:
    puzzle_games=[compact_game(row) for row in json.loads(puzzle_games_match.group(1))]
playable_games=quality.playable_games(games)
clues_match=re.search(r'const clueSpecs=(\[.*?\]);\nconst clues=',text,re.S)
if not clues_match:
    print('ERROR: unable to read clue definitions from generated catalogue asset');sys.exit(1)
clue_specs={spec['id']:spec for spec in json.loads(clues_match.group(1))}
if report.get('catalogHash')!=manifest.get('catalogHash') or report.get('buildHash')!=manifest.get('buildHash') or report.get('dataAsset')!=asset or report.get('indexAsset')!=index_asset or report.get('searchAsset')!=search_asset or report.get('detailsAsset')!=details_asset or report.get('detailsHash')!=details_hash:
    errors.append('catalogue report and manifest disagree')
if f'"catalogHash":"{manifest.get("catalogHash","")}"' not in text or f'"buildHash":"{manifest.get("buildHash","")}"' not in text:
    errors.append('catalogue data and manifest disagree')
if f'"detailsAsset":"{details_asset}"' not in text:
    errors.append('catalogue data and manifest details assets disagree')
if report.get('puzzleGameCount')!=len(puzzle_games):
    errors.append('catalogue report puzzle bootstrap count does not match generated data')
if report.get('searchableGameCount')!=len(puzzle_games):
    errors.append('catalogue report searchable-game count does not match generated data')
if not {game['id'] for game in puzzle_games}.issubset({game['id'] for game in games}):
    errors.append('puzzle bootstrap contains a game missing from the full index')
if {game['id'] for game in puzzle_games}!={game['id'] for game in games}:
    errors.append('search index and puzzle bootstrap contain different game sets')
if report['games']<20000:errors.append('expected at least 20,000 games; catalogue may have been truncated')
if report.get('selection')!='all eligible source records (no popularity cap)':errors.append('catalogue report does not confirm uncapped source selection')
clue_counts=report.get('clueCounts',{})
# Source game files store genre/platform IDs.  A missing lookup join leaves the
# catalogue numerically large but makes genre intersections effectively empty.
if clue_counts.get('adventure',0)<10000:errors.append('Adventure coverage is unexpectedly low; genre IDs may not have been resolved')
if clue_counts.get('xbox',0)<5000:errors.append('Xbox coverage is unexpectedly low; platform IDs may not have been resolved')
# The compact browser index is deliberately the curated answer set, not the
# entire raw source catalogue.  Recheck the searchable metrics against it, and
# keep the raw-source quality floors backed by the build report generated while
# the full source records were still available.
coverage=quality.metadata_coverage(games)
if report.get('searchableMetadataCoverage')!=coverage:
    errors.append('catalogue report searchable metadata coverage does not match generated data')
if report.get('searchablePlatformCounts')!=quality.platform_counts(games):
    errors.append('catalogue report searchable platform counts do not match generated data')
if report.get('searchablePool')!=quality.playable_pool_report(games):
    errors.append('catalogue report searchable playable-pool summary does not match generated data')
raw_coverage=report.get('metadataCoverage',{})
for field,minimum in quality.METADATA_COVERAGE_THRESHOLDS.items():
    if not isinstance(raw_coverage.get(field),dict) or raw_coverage[field].get('coverage',0)<minimum:
        errors.append(f'{field} coverage is below the raw-catalogue quality floor')
raw_platform_counts=report.get('platformCounts',{})
for platform,minimum in quality.PLATFORM_MINIMUMS.items():
    if raw_platform_counts.get(platform,0)<minimum:
        errors.append(f'{platform} platform coverage is below the raw-catalogue quality floor')
if not 40<=report['clues']<=5000:errors.append('expected 40–5,000 clue types')
if report['puzzles']<90:errors.append('expected at least 90 daily puzzles')
for mode in ('Classic','Retro','Modern','Nintendo','PlayStation','Xbox','Deep Cut','Trial'):
    if not report.get('modes',{}).get(mode,{}).get('puzzles'):
        errors.append(f'missing generated puzzles for {mode} mode')
if report.get('modes',{}).get('Trial',{}).get('makerCriteria',0)<3:
    errors.append('Trial mode does not have at least three usable maker criteria')
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
# Recalculate every generated intersection from the curated pool.  This makes
# it impossible to report a curated count while accidentally using the raw
# search index to build the puzzle.
puzzles_match=re.search(r'const puzzles=(\[.*?\]);\nreturn ',text,re.S)
if not puzzles_match:
    errors.append('unable to read generated puzzles from catalogue asset')
else:
    indexed={}
    family_usage={}
    for puzzle in json.loads(puzzles_match.group(1)):
        if puzzle['mode'] not in indexed:
            indexed[puzzle['mode']]=modes.build_index(playable_games,puzzle['mode'])[3]
        pairs=indexed[puzzle['mode']]
        expected=[len(modes.pair_lookup(pairs,row,col)) for row in puzzle['rows'] for col in puzzle['cols']]
        if puzzle['answerCounts']!=expected:
            errors.append(f'puzzle {puzzle["id"]} was not generated from the playable pool')
        selected_specs=[clue_specs[criterion] for criterion in puzzle['rows']+puzzle['cols']]
        if not puzzle_rules.balanced_families(selected_specs):
            errors.append(f'puzzle {puzzle["id"]} does not use the balanced knowledge-family mix')
        if puzzle.get('difficulty')!=puzzle_rules.difficulty_for(puzzle['answerCounts']):
            errors.append(f'puzzle {puzzle["id"]} difficulty is not based on its smallest answer pool')
        if puzzle['mode'] in puzzle_rules.STANDARD_MODES and puzzle['date']>puzzle_rules.published_through().isoformat() and min(puzzle['answerCounts'])<puzzle_rules.STANDARD_MIN_ANSWERS:
            errors.append(f"future {puzzle['mode']} puzzle {puzzle['id']} has fewer than {puzzle_rules.STANDARD_MIN_ANSWERS} answers in a cell")
        families=('maker',)+puzzle_rules.CORE_FAMILIES if puzzle['mode']=='Trial' else puzzle_rules.CORE_FAMILIES
        usage=family_usage.setdefault(puzzle['mode'],{family:0 for family in families})
        for spec in selected_specs:
            usage[puzzle_rules.clue_family(spec)]+=1
    for mode,usage in family_usage.items():
        total=sum(usage.values())
        if mode=='Trial':
            maker_ratio=usage.get('maker',0)/total if total else 0
            if not .49<=maker_ratio<=.51:
                errors.append(f'{mode} maker criteria are not balanced: {usage.get("maker",0)}/{total}')
        else:
            for family,count in usage.items():
                if not .19<=count/total<=.21:
                    errors.append(f'{mode} {family} criteria are not balanced: {count}/{total}')
# A release-era smoke test.  These titles span the requested last twenty years
# and catch both a truncated source catalogue and an outdated source snapshot.
spot_checks=['Gears of War','BioShock','Mass Effect','Grand Theft Auto IV','Demon’s Souls','Red Dead Redemption','The Elder Scrolls V: Skyrim','The Last of Us','Grand Theft Auto V','The Witcher 3: Wild Hunt','The Legend of Zelda: Breath of the Wild','Red Dead Redemption 2','Death Stranding','Animal Crossing: New Horizons','Elden Ring','Baldur’s Gate 3','Alan Wake 2','Astro Bot','Clair Obscur: Expedition 33']
titles={game['title'] for game in games}
for title in spot_checks:
    if title not in titles:errors.append(f'missing required catalogue spot-check: {title}')
if errors:
    print('\n'.join('ERROR: '+x for x in errors));sys.exit(1)
print(f"Validated {report['games']:,} games, {report['clues']} clues and {report['puzzles']} puzzles ({report['first']} to {report['last']}).")
