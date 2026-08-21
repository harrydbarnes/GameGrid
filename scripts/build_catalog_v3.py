#!/usr/bin/env python3
import datetime as dt, hashlib, json, random, statistics
import build_catalog as base
import build_catalog_v2 as v2
import catalog_quality as quality

START=base.START
END=base.END
MODES=v2.MODES


def fingerprint(value):
    """Return a short, stable fingerprint for a JSON-compatible value."""
    payload=json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False)
    return hashlib.sha256(payload.encode('utf-8')).hexdigest()[:16]


def catalogue_hash(games,clue_specs):
    return fingerprint({'games':games,'clues':clue_specs})


def version_puzzles(puzzles,expected_catalogue_hash):
    """Stamp every puzzle with the catalogue it was generated against."""
    build_hash=fingerprint({'catalogHash':expected_catalogue_hash,'puzzles':puzzles})
    for puzzle in puzzles:
        puzzle['catalogHash']=expected_catalogue_hash
        puzzle['buildHash']=build_hash
    return expected_catalogue_hash,build_hash


def pair_lookup(pair_sets,a,b):
    return pair_sets.get((a,b) if a<b else (b,a),set())


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


def make_puzzle(mode,date,pid,recent,pool,pair_sets,rng,scoped_games):
    if len(pool)<6:
        raise RuntimeError(f'{mode} has only {len(pool)} eligible clues; need at least 6')
    best=None
    for level,attempts in enumerate((5000,12000,25000)):
        low,high,min_distinct,max_reuse=limits(mode,level,scoped_games)
        for _ in range(attempts):
            six=rng.sample(pool,6);rows=six[:3];cols=six[3:];ids=[s['id'] for s in six]
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
            if level==0 and q<8:break
        if best:break
    if not best:
        raise RuntimeError(f'Could not build a valid {mode} puzzle for {date} after progressive search')
    q,rows,cols,ints,distinct,level=best
    med=statistics.median(ints)
    difficulty='Hard' if mode=='Deep Cut' or med<18 else ('Easy' if med>70 else 'Medium')
    return {'id':pid,'date':date.isoformat(),'mode':mode,'scope':mode,'difficulty':difficulty,'rows':[x['id'] for x in rows],'cols':[x['id'] for x in cols],'answerCounts':ints,'solutionPool':distinct,'qualityScore':round(q-(level*100),2),'generationLevel':level}


def generate(games):
    all_puzzles=[];report_modes={};pid=1
    for mi,mode in enumerate(MODES):
        scoped_ids,counts,pool,pair_sets=v2.build_index(games,mode)
        print(f'Generating {mode}: {len(scoped_ids)} scoped games, {len(pool)} clues')
        rng=random.Random(260817+mi*997);recent=[];d=START;mode_ps=[]
        while d<=END:
            p=make_puzzle(mode,d,pid,recent,pool,pair_sets,rng,len(scoped_ids));pid+=1
            mode_ps.append(p);recent=(recent+[tuple(p['rows']+p['cols'])])[-45:];d+=dt.timedelta(days=1)
        all_puzzles+=mode_ps
        medians=[statistics.median(p['answerCounts']) for p in mode_ps]
        report_modes[mode]={'puzzles':len(mode_ps),'scopedGames':len(scoped_ids),'medianAnswersPerSquare':round(statistics.median(medians),1),'minAnswers':min(min(p['answerCounts']) for p in mode_ps),'maxAnswers':max(max(p['answerCounts']) for p in mode_ps),'relaxedPuzzles':sum(p.get('generationLevel',0)>0 for p in mode_ps)}
    all_puzzles.sort(key=lambda p:(p['date'],MODES.index(p['mode'])))
    return all_puzzles,report_modes


def main():
    games=base.build_games()
    if len(games)<4000:raise RuntimeError(f'Catalogue too small: {len(games)}')
    puzzles,mode_report=generate(games)
    catalog_hash,build_hash=version_puzzles(puzzles,catalogue_hash(games,base.CLUE_SPECS))
    data_asset=f'data.{build_hash}.js'
    clue_counts={s['id']:sum(base.match(g,s) for g in games) for s in base.CLUE_SPECS}
    meta={'gameCount':len(games),'clueCount':len(base.CLUE_SPECS),'puzzleCount':len(puzzles),'modes':MODES,'source':'PlayMyData (IGDB-derived)','catalogHash':catalog_hash,'buildHash':build_hash,'dataAsset':data_asset}
    out="window.GAMEGRID_DATA=(()=>{\nconst games="+json.dumps(games,separators=(',',':'),ensure_ascii=False)+";\n"+base.js_clues()+"\nconst puzzles="+json.dumps(puzzles,separators=(',',':'))+";\nreturn {games,clues,puzzles,meta:"+json.dumps(meta,separators=(',',':'))+"};\n})();\n"
    open(data_asset,'w',encoding='utf-8').write(out)
    manifest={'catalogHash':catalog_hash,'buildHash':build_hash,'dataAsset':data_asset}
    open('catalog-manifest.js','w',encoding='utf-8').write('window.GAMEGRID_CATALOG_MANIFEST='+json.dumps(manifest,separators=(',',':'))+';\n')
    # Keep index.html stable while making its parser-blocking data hook load the
    # current manifest and its immutable, fingerprinted payload.
    open('data.js','w',encoding='utf-8').write("document.write('<script src=\"./catalog-manifest.js\"><\\/script><script src=\"./catalog-loader.js\"><\\/script>');\n")
    report={'games':len(games),'clues':len(base.CLUE_SPECS),'puzzles':len(puzzles),'modes':mode_report,'first':START.isoformat(),'last':END.isoformat(),'clueCounts':clue_counts,'selection':'all eligible source records (no popularity cap)','essentialBackfill':len(base.ESSENTIAL_GAMES),'catalogHash':catalog_hash,'buildHash':build_hash,'dataAsset':data_asset,'metadataCoverage':quality.metadata_coverage(games),'platformCounts':quality.platform_counts(games)}
    open('catalog-report.json','w').write(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
