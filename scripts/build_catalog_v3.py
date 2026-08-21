#!/usr/bin/env python3
import datetime as dt, gzip, hashlib, json, os, random, statistics
import build_catalog as base
import build_catalog_v2 as v2
import catalog_quality as quality

START=base.START
END=base.END
MODES=v2.MODES
CORE_FAMILIES=('platform','genre','era','rating','title')
ASSET_KEYS=('dataAsset','indexAsset','searchAsset','detailsAsset')

# The current production split is roughly 9.2 MB uncompressed. Keep enough
# headroom for catalogue growth without allowing the initial/search payload to
# drift back towards the old 23 MB all-in-one asset.
PERFORMANCE_BUDGETS={
    'puzzleIndexBytes':12_000_000,
    'puzzleIndexGzipBytes':3_000_000,
}


def clue_family(spec):
    kind=spec.get('kind','')
    if kind in {'platform','platformAny'}: return 'platform'
    if kind=='yearRange': return 'era'
    if kind=='genre': return 'genre'
    if kind=='rating': return 'rating'
    if kind.startswith('title'): return 'title'
    return 'other'


def difficulty_for(answer_counts):
    """Label a grid by its least forgiving square, never by its median."""
    minimum=min(answer_counts,default=0)
    if minimum>=20: return 'Easy'
    if minimum>=8: return 'Medium'
    return 'Hard'


def balanced_families(specs):
    families=[clue_family(spec) for spec in specs]
    return (
        len(specs)==6
        and all(family in families for family in CORE_FAMILIES)
        and sum(spec.get('kind')=='titleInitial' for spec in specs)<=1
    )


def family_buckets(pool):
    return {family:[spec for spec in pool if clue_family(spec)==family] for family in CORE_FAMILIES}


def balanced_six(buckets,family_usage,rng):
    """Pick five core knowledge families, then rotate the sixth fairly."""
    if any(not candidates for candidates in buckets.values()):
        return None
    selected=[]
    for family in CORE_FAMILIES:
        candidates=buckets[family]
        # Initial-letter clues are deliberately seasoning: use a substantive
        # title property whenever one is available for the title slot.
        if family=='title':
            substantive=[spec for spec in candidates if spec.get('kind')!='titleInitial']
            candidates=substantive or candidates
        selected.append(rng.choice(candidates))
    lowest=min(family_usage.get(family,0) for family in CORE_FAMILIES)
    extra_families=[family for family in CORE_FAMILIES if family_usage.get(family,0)==lowest]
    extra_family=rng.choice(extra_families)
    candidates=[spec for spec in buckets[extra_family] if spec not in selected]
    if extra_family=='title' and any(spec.get('kind')=='titleInitial' for spec in selected):
        candidates=[spec for spec in candidates if spec.get('kind')!='titleInitial']
    if not candidates:
        return None
    selected.append(rng.choice(candidates))
    return selected


def fingerprint(value):
    """Return a short, stable fingerprint for a JSON-compatible value."""
    payload=json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False)
    return hashlib.sha256(payload.encode('utf-8')).hexdigest()[:16]


def content_fingerprint(value):
    """Return a short fingerprint for the exact bytes published to clients."""
    payload=value.encode('utf-8') if isinstance(value,str) else bytes(value)
    return hashlib.sha256(payload).hexdigest()[:16]


def details_asset_name(details_text):
    """Name the deferred details asset from its final serialized contents."""
    return f'details.{content_fingerprint(details_text)}.js'


def catalogue_hash(games,clue_specs):
    return fingerprint({'games':games,'clues':clue_specs})


def catalogue_assets(build_hash):
    return {'dataAsset':f'puzzle.{build_hash}.js','indexAsset':f'index.{build_hash}.js','searchAsset':f'search.{build_hash}.js','detailsAsset':f'details.{build_hash}.js'}


def asset_sizes(assets,root='.'):
    """Return raw and deterministic gzip sizes for generated catalogue assets."""
    sizes={}
    for key in ASSET_KEYS:
        name=assets.get(key)
        if not name:
            raise ValueError(f'missing catalogue asset name: {key}')
        with open(os.path.join(root,name),'rb') as handle:
            payload=handle.read()
        sizes[key]={'file':name,'bytes':len(payload),'gzipBytes':len(gzip.compress(payload,mtime=0))}
    puzzle_index={key:sizes[key] for key in ('dataAsset','indexAsset')}
    sizes['puzzleIndex']={
        'bytes':sum(item['bytes'] for item in puzzle_index.values()),
        'gzipBytes':sum(item['gzipBytes'] for item in puzzle_index.values()),
        'assets':['dataAsset','indexAsset'],
    }
    return sizes


def performance_budget_errors(sizes,budgets=PERFORMANCE_BUDGETS):
    """Describe any puzzle-plus-index budget violations without mutating files."""
    total=sizes.get('puzzleIndex') if isinstance(sizes,dict) else None
    if not isinstance(total,dict):
        return ['puzzle + index size report is missing']
    errors=[]
    if total.get('bytes',0)>budgets['puzzleIndexBytes']:
        errors.append(f"puzzle + index uncompressed size {total.get('bytes',0):,} exceeds {budgets['puzzleIndexBytes']:,} bytes")
    if total.get('gzipBytes',0)>budgets['puzzleIndexGzipBytes']:
        errors.append(f"puzzle + index gzip size {total.get('gzipBytes',0):,} exceeds {budgets['puzzleIndexGzipBytes']:,} bytes")
    return errors


def enforce_performance_budgets(sizes,budgets=PERFORMANCE_BUDGETS):
    errors=performance_budget_errors(sizes,budgets)
    if errors:
        raise RuntimeError('Catalogue performance budget failed: '+'; '.join(errors))


def compact_index(games):
    """Search/matching fields only; rich display data is deferred."""
    return [[g['id'],g['title'],g['year'],g['platforms'],g['tags'],g['rating'],g['ratingsCount']] for g in games]


def search_worker(index_asset):
    """Search the full compact index off the main thread after first use."""
    index_literal=json.dumps('./'+index_asset)
    return """const INDEX_ASSET="""+index_literal+""";
importScripts(INDEX_ASSET);
const rows=Array.isArray(self.GAMEGRID_INDEX)?self.GAMEGRID_INDEX:[];
function normalise(value){return String(value??'').toLowerCase().normalize('NFD').replace(/[\\u0300-\\u036f]/g,'').replace(/[^a-z0-9 ]/g,' ').replace(/\\s+/g,' ').trim()}
function popularity(row){return Math.log10(Number(row[6]||0)+1)*12+Number(row[5]||0)/10+(Number(row[2])>=2015?2:0)}
function searchScore(row,q){const title=normalise(row[1]),words=title.split(' '),queryWords=q.split(' ').filter(Boolean);if(title===q)return 10000;if(title.startsWith(q))return 8000-q.length;if(words.some(word=>word===q))return 7000;if(words.some(word=>word.startsWith(q)))return 6200;const position=title.indexOf(q);if(position>=0)return 5000-position;if(queryWords.every(word=>title.includes(word)))return 3500+queryWords.reduce((score,word)=>score+(words.some(item=>item.startsWith(word))?50:0),0);return -1}
self.postMessage({type:'ready',count:rows.length});
self.onmessage=event=>{const message=event.data||{};if(message.type!=='search')return;const query=normalise(message.query),excluded=new Set(message.excluded||[]);let list=rows.filter(row=>!excluded.has(row[0]));if(query)list=list.map(row=>({row,score:searchScore(row,query)+popularity(row)})).filter(item=>item.score>=0).sort((a,b)=>b.score-a.score||Number(b.row[6]||0)-Number(a.row[6]||0)||String(a.row[1]).localeCompare(String(b.row[1]))).map(item=>item.row);else list=list.sort((a,b)=>popularity(b)-popularity(a)||String(a[1]).localeCompare(String(b[1])));self.postMessage({type:'results',id:message.id,rows:list.slice(0,20)});};
"""


def detail_index(games):
    return {g['id']:{key:g[key] for key in ('developers','publishers','franchise','coverUrl') if g.get(key)} for g in games if any(g.get(key) for key in ('developers','publishers','franchise','coverUrl'))}


def version_puzzles(puzzles,expected_catalogue_hash,payload=None):
    """Stamp every puzzle with the catalogue it was generated against."""
    build_hash=fingerprint({'catalogHash':expected_catalogue_hash,'puzzles':puzzles,'payload':payload})
    for puzzle in puzzles:
        puzzle['catalogHash']=expected_catalogue_hash
        puzzle['buildHash']=build_hash
    return expected_catalogue_hash,build_hash


def pair_lookup(pair_sets,a,b):
    return pair_sets.get((a,b) if a<b else (b,a),set())


def game_ids_for_pair(games,pair_sets,a,b):
    """Translate v2's positional pair-set members back to stable game IDs."""
    return {games[index]['id'] for index in pair_lookup(pair_sets,a,b)}


def scale_for(scoped_games):
    # The original limits were calibrated for a 6,000-game catalogue.  Grow
    # them sub-linearly: a larger index gets broader answer pools without
    # turning every platform/genre intersection into a trivial catch-all.
    return max(1.0,(scoped_games/6000)**0.5)


def limits(mode,level,scoped_games):
    scale=scale_for(scoped_games)
    # Each level remains valid, but progressively relaxes puzzle aesthetics so the build never fails just because a random search is unlucky.
    if level==0:
        if mode=='Deep Cut': return 3,round(45*scale),round(18*scale),3
        if mode in {'Nintendo','PlayStation','Xbox','Retro','Modern'}: return 4,round(180*scale),round(30*scale),3
        return 5,round(300*scale),round(30*scale),3
    if level==1:
        if mode=='Deep Cut': return 3,round(70*scale),round(15*scale),4
        if mode in {'Nintendo','PlayStation','Xbox','Retro','Modern'}: return 3,round(260*scale),round(22*scale),4
        return 3,round(420*scale),round(22*scale),4
    if mode=='Deep Cut': return 3,round(120*scale),round(12*scale),6
    return 3,round(600*scale),round(15*scale),6


def score_counts(ints,mode,scoped_games):
    med=statistics.median(ints);spread=max(ints)-min(ints);target=(18 if mode=='Deep Cut' else 45)*scale_for(scoped_games)
    return abs(med-target)+(spread*0.08)


def make_puzzle(mode,date,pid,recent,pool,pair_sets,rng,scoped_games,family_usage):
    if len(pool)<6:
        raise RuntimeError(f'{mode} has only {len(pool)} eligible clues; need at least 6')
    buckets=family_buckets(pool)
    best=None
    for level,attempts in enumerate((5000,12000,25000)):
        low,high,min_distinct,max_reuse=limits(mode,level,scoped_games)
        for _ in range(attempts):
            six=balanced_six(buckets,family_usage,rng)
            if not six: break
            rng.shuffle(six);rows=six[:3];cols=six[3:];ids=[s['id'] for s in six]
            if not balanced_families(six):continue
            if tuple(ids) in recent:continue
            if any(r['kind']==c['kind'] and r['value']==c['value'] for r in rows for c in cols):continue
            cells=[pair_lookup(pair_sets,r['id'],c['id']) for r in rows for c in cols]
            ints=[len(c) for c in cells]
            if min(ints)<low or max(ints)>high:continue
            distinct=len(set().union(*cells))
            if distinct<min_distinct:continue
            freq={};bad=False
            for cell in cells:
                for gid in cell:
                    freq[gid]=freq.get(gid,0)+1
                    if freq[gid]>max_reuse:
                        bad=True;break
                if bad:break
            if bad:continue
            q=score_counts(ints,mode,scoped_games)+(level*100)
            if best is None or q<best[0]:best=(q,rows,cols,ints,distinct,level)
            # Once a balanced grid is close to the target answer-pool shape,
            # further random searching has negligible player benefit but makes
            # a full multi-mode catalogue build needlessly slow.
            if level==0 and q<30:break
        if best:break
    if not best:
        raise RuntimeError(f'Could not build a valid {mode} puzzle for {date} after progressive search')
    q,rows,cols,ints,distinct,level=best
    difficulty=difficulty_for(ints)
    return {'id':pid,'date':date.isoformat(),'mode':mode,'scope':mode,'difficulty':difficulty,'rows':[x['id'] for x in rows],'cols':[x['id'] for x in cols],'answerCounts':ints,'solutionPool':distinct,'qualityScore':round(q-(level*100),2),'generationLevel':level}


def generate(games):
    all_puzzles=[];report_modes={};puzzle_game_ids=set();pid=1
    for mi,mode in enumerate(MODES):
        scoped_ids,counts,pool,pair_sets=v2.build_index(games,mode)
        print(f'Generating {mode}: {len(scoped_ids)} scoped games, {len(pool)} clues')
        rng=random.Random(260817+mi*997);recent=[];family_usage={family:0 for family in CORE_FAMILIES};d=START;mode_ps=[]
        while d<=END:
            p=make_puzzle(mode,d,pid,recent,pool,pair_sets,rng,len(scoped_ids),family_usage);pid+=1
            for row in p['rows']:
                for col in p['cols']:
                    puzzle_game_ids.update(game_ids_for_pair(games,pair_sets,row,col))
            for criterion in p['rows']+p['cols']:
                family_usage[clue_family(next(spec for spec in pool if spec['id']==criterion))]+=1
            mode_ps.append(p);recent=(recent+[tuple(p['rows']+p['cols'])])[-45:];d+=dt.timedelta(days=1)
        all_puzzles+=mode_ps
        medians=[statistics.median(p['answerCounts']) for p in mode_ps]
        report_modes[mode]={'puzzles':len(mode_ps),'scopedGames':len(scoped_ids),'medianAnswersPerSquare':round(statistics.median(medians),1),'minAnswers':min(min(p['answerCounts']) for p in mode_ps),'maxAnswers':max(max(p['answerCounts']) for p in mode_ps),'familyUsage':family_usage,'relaxedPuzzles':sum(p.get('generationLevel',0)>0 for p in mode_ps)}
    all_puzzles.sort(key=lambda p:(p['date'],MODES.index(p['mode'])))
    return all_puzzles,report_modes,puzzle_game_ids


def main():
    games=base.build_games()
    if len(games)<4000:raise RuntimeError(f'Catalogue too small: {len(games)}')
    # Keep the complete index for answer search, but only let entries with
    # usable metadata and a small real-world participation signal shape grids.
    playable_games=quality.playable_games(games)
    if len(playable_games)<4000:raise RuntimeError(f'Playable catalogue too small: {len(playable_games)}')
    puzzles,mode_report,puzzle_game_ids=generate(playable_games)
    puzzle_games=[game for game in games if game['id'] in puzzle_game_ids]
    catalog_hash=catalogue_hash(games,base.CLUE_SPECS)
    _,build_hash=version_puzzles(puzzles,catalog_hash,{'puzzleGameIds':sorted(puzzle_game_ids)})
    assets=catalogue_assets(build_hash)
    data_asset=assets['dataAsset']
    # Preserve raw-index coverage telemetry separately from the curated counts
    # used by the generator. The former catches failed lookup joins; the latter
    # explains the playable puzzle pool without conflating the two.
    clue_counts={s['id']:sum(base.match(g,s) for g in games) for s in base.CLUE_SPECS}
    playable_clue_counts={s['id']:sum(base.match(g,s) for g in playable_games) for s in base.CLUE_SPECS}
    details_payload={'catalogHash':catalog_hash,'buildHash':build_hash,'games':detail_index(games)}
    details_text='window.GAMEGRID_DETAILS='+json.dumps(details_payload,separators=(',',':'),ensure_ascii=False)+';\n'
    assets['detailsAsset']=details_asset_name(details_text)
    details_hash=content_fingerprint(details_text)
    meta={'gameCount':len(games),'puzzleGameCount':len(puzzle_games),'playableGameCount':len(playable_games),'clueCount':len(base.CLUE_SPECS),'puzzleCount':len(puzzles),'modes':MODES,'source':'PlayMyData (IGDB-derived)','catalogHash':catalog_hash,'buildHash':build_hash,**assets}
    puzzle_index=json.dumps(compact_index(puzzle_games),separators=(',',':'),ensure_ascii=False)
    out="window.GAMEGRID_DATA=(()=>{\nconst games="+puzzle_index+".map(([id,title,year,platforms,tags,rating,ratingsCount])=>({id,title,year,platforms,tags,rating,ratingsCount,developers:[],publishers:[]}));\n"+base.js_clues()+"\nconst puzzles="+json.dumps(puzzles,separators=(',',':'))+";\nreturn {games,clues,puzzles,meta:"+json.dumps(meta,separators=(',',':'))+"};\n})();\n"
    open(data_asset,'w',encoding='utf-8').write(out)
    open(assets['indexAsset'],'w',encoding='utf-8').write('globalThis.GAMEGRID_INDEX='+json.dumps(compact_index(games),separators=(',',':'),ensure_ascii=False)+';\n')
    open(assets['searchAsset'],'w',encoding='utf-8').write(search_worker(assets['indexAsset']))
    open(assets['detailsAsset'],'w',encoding='utf-8').write(details_text)
    sizes=asset_sizes(assets)
    enforce_performance_budgets(sizes)
    manifest={'catalogHash':catalog_hash,'buildHash':build_hash,'detailsHash':details_hash,**assets}
    open('catalog-manifest.js','w',encoding='utf-8').write('window.GAMEGRID_CATALOG_MANIFEST='+json.dumps(manifest,separators=(',',':'))+';\n')
    # Keep index.html stable while making its parser-blocking data hook load the
    # current manifest and its immutable, fingerprinted payload.
    open('data.js','w',encoding='utf-8').write("document.write('<script src=\"./catalog-manifest.js\"><\\/script><script src=\"./catalog-loader.js\"><\\/script>');\n")
    report={'games':len(games),'puzzleGameCount':len(puzzle_games),'clues':len(base.CLUE_SPECS),'puzzles':len(puzzles),'modes':mode_report,'first':START.isoformat(),'last':END.isoformat(),'clueCounts':clue_counts,'playableClueCounts':playable_clue_counts,'selection':'all eligible source records (no popularity cap)','playablePool':quality.playable_pool_report(games),'essentialBackfill':len(base.ESSENTIAL_GAMES),'catalogHash':catalog_hash,'buildHash':build_hash,'detailsHash':details_hash,**assets,'assetSizes':sizes,'performanceBudgets':PERFORMANCE_BUDGETS,'metadataCoverage':quality.metadata_coverage(games),'platformCounts':quality.platform_counts(games)}
    open('catalog-report.json','w').write(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
