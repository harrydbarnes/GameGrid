#!/usr/bin/env python3
import datetime as dt, itertools, json, random, statistics
import build_catalog as base

START=base.START
END=base.END
MODES=['Classic','Retro','Nintendo','PlayStation','Xbox','Deep Cut']
NINTENDO={'Switch','Switch 2','Wii U','Wii','GameCube','Nintendo 64','SNES','NES','Game Boy Advance','Game Boy Color','Game Boy','Nintendo DS','Nintendo 3DS','Nintendo platform'}


def scope_ok(g,mode):
    if mode in {'Classic','Deep Cut'}: return True
    if mode=='Retro': return g['year']<=2009
    if mode=='Nintendo': return any(p in NINTENDO for p in g['platforms'])
    if mode=='PlayStation': return any(p.startswith('PlayStation') or p in {'PSP','PS Vita'} for p in g['platforms'])
    if mode=='Xbox': return any(p.startswith('Xbox') for p in g['platforms'])
    return True


def clue_pool(mode,counts):
    specs=[s for s in base.CLUE_SPECS if 20<=counts.get(s['id'],0)<=5000]
    if mode=='Classic': return specs
    if mode=='Retro':
        excluded={'y2020s','post2015','switch2','ps5','ps4','xseries','xone'}
        return [s for s in specs if s['id'] not in excluded]
    if mode=='Nintendo':
        ids={'switch','switch2','wiiu','wii','gamecube','n64','snes','nes','gba','gbc','gb','ds','3ds','y1990s','y2000s','y2010s','y2020s','pre2000','rpg','shooter','strategy','racing','sport','fighting','platformer','puzzle','adventure','simulation','indie','arcade','oneword','numbertitle','lettera','letterg','letterm','letters','rating70','rating80','rating85'}
        return [s for s in specs if s['id'] in ids]
    if mode=='PlayStation':
        ids={'ps1','ps2','ps3','ps4','ps5','y1990s','y2000s','y2010s','y2020s','pre2000','post2015','rpg','shooter','strategy','racing','sport','fighting','platformer','puzzle','adventure','simulation','indie','arcade','oneword','numbertitle','lettera','letterg','letterm','letters','rating70','rating80','rating85','rating90'}
        return [s for s in specs if s['id'] in ids]
    if mode=='Xbox':
        ids={'xboxoriginal','x360','xone','xseries','y2000s','y2010s','y2020s','post2015','rpg','shooter','strategy','racing','sport','fighting','platformer','puzzle','adventure','simulation','indie','arcade','oneword','numbertitle','lettera','letterg','letterm','letters','rating70','rating80','rating85','rating90'}
        return [s for s in specs if s['id'] in ids]
    if mode=='Deep Cut':
        return [s for s in specs if s['id'] not in {'pc','playstation','xbox','nintendo','rating70'}]
    return specs


def bounds(mode,relaxed=False):
    if mode=='Deep Cut': return (3,80 if relaxed else 45)
    if mode in {'Nintendo','PlayStation','Xbox','Retro'}: return (3 if relaxed else 4,320 if relaxed else 180)
    return (3 if relaxed else 5,500 if relaxed else 300)


def quality(ints,mode,relaxed=False):
    if not ints:return None
    low,high=bounds(mode,relaxed)
    if min(ints)<low or max(ints)>high:return None
    med=statistics.median(ints);spread=max(ints)-min(ints);target=18 if mode=='Deep Cut' else 45
    return abs(med-target)+(spread*0.08)


def build_index(games,mode):
    scoped_ids={i for i,g in enumerate(games) if scope_ok(g,mode)}
    clue_sets={spec['id']:{i for i in scoped_ids if base.match(games[i],spec)} for spec in base.CLUE_SPECS}
    counts={cid:len(ids) for cid,ids in clue_sets.items()}
    pool=clue_pool(mode,counts)
    pair_sets={}
    for a,b in itertools.combinations(pool,2):
        pair_sets[tuple(sorted((a['id'],b['id'])))]=clue_sets[a['id']] & clue_sets[b['id']]
    return scoped_ids,counts,pool,pair_sets


def pair_lookup(pair_sets,a,b):
    return pair_sets.get(tuple(sorted((a,b))),set())


def structurally_ok(rows,cols):
    if len({x['id'] for x in rows+cols})<6:return False
    return not any(r['kind']==c['kind'] and r['value']==c['value'] for r in rows for c in cols)


def evaluate(rows,cols,pair_sets,mode,relaxed=False,allow_reuse=False):
    if not structurally_ok(rows,cols):return None
    cells=[pair_lookup(pair_sets,r['id'],c['id']) for r in rows for c in cols]
    ints=[len(x) for x in cells]
    q=quality(ints,mode,relaxed)
    if q is None:return None
    distinct=len(set().union(*cells))
    min_distinct=12 if relaxed else (18 if mode=='Deep Cut' else 30)
    if distinct<min_distinct:return None
    if not allow_reuse:
        frequency={}
        for cell in cells:
            for gid in cell:
                frequency[gid]=frequency.get(gid,0)+1
                if frequency[gid]>3:return None
    return q,ints,distinct


def random_search(mode,recent,pool,pair_sets,rng,relaxed=False):
    best=None
    attempts=2200 if not relaxed else 3500
    for _ in range(attempts):
        six=rng.sample(pool,6);rows=six[:3];cols=six[3:]
        if tuple(x['id'] for x in six) in recent:continue
        ev=evaluate(rows,cols,pair_sets,mode,relaxed=relaxed,allow_reuse=relaxed)
        if not ev:continue
        q,ints,distinct=ev
        if best is None or q<best[0]:best=(q,rows,cols,ints,distinct,'relaxed-random' if relaxed else 'quality-random')
        if q<(15 if relaxed else 8):break
    return best


def deterministic_search(mode,pool,pair_sets):
    """Find a valid K3,3 clue arrangement deterministically.
    This guarantees we do not fail merely because RNG missed an existing valid grid.
    """
    low,high=bounds(mode,True)
    target=18 if mode=='Deep Cut' else 45
    # Precompute valid neighbours for every clue under relaxed but still playable bounds.
    neighbours={s['id']:[] for s in pool}
    by_id={s['id']:s for s in pool}
    for a,b in itertools.combinations(pool,2):
        n=len(pair_lookup(pair_sets,a['id'],b['id']))
        if low<=n<=high:
            neighbours[a['id']].append((b['id'],n));neighbours[b['id']].append((a['id'],n))
    row_candidates=sorted(pool,key=lambda s:len(neighbours[s['id']]),reverse=True)
    best=None
    # Enumerating row triples is small: ~10k at a 40-clue pool.
    for rows in itertools.combinations(row_candidates,3):
        row_ids={r['id'] for r in rows}
        common=set(x[0] for x in neighbours[rows[0]['id']])
        common&=set(x[0] for x in neighbours[rows[1]['id']])
        common&=set(x[0] for x in neighbours[rows[2]['id']])
        common-=row_ids
        cols=[by_id[cid] for cid in common if cid in by_id]
        if len(cols)<3:continue
        # Prefer columns whose three intersections are near the target, then test a small deterministic shortlist.
        def col_score(c):
            vals=[len(pair_lookup(pair_sets,r['id'],c['id'])) for r in rows]
            return sum(abs(v-target) for v in vals)
        cols=sorted(cols,key=col_score)[:14]
        for chosen in itertools.combinations(cols,3):
            if not structurally_ok(list(rows),list(chosen)):continue
            cells=[pair_lookup(pair_sets,r['id'],c['id']) for r in rows for c in chosen]
            ints=[len(x) for x in cells]
            if min(ints)<3:continue
            distinct=len(set().union(*cells))
            if distinct<9:continue
            # Final fallback deliberately relaxes duplicate-solution pressure, but never answer validity.
            med=statistics.median(ints);spread=max(ints)-min(ints)
            q=abs(med-target)+(spread*0.08)+25
            cand=(q,list(rows),list(chosen),ints,distinct,'deterministic-fallback')
            if best is None or q<best[0]:best=cand
            if q<35:return best
    return best


def build_mode_puzzle(mode,date,pid,recent,pool,pair_sets,rng):
    best=random_search(mode,recent,pool,pair_sets,rng,False)
    if not best:best=random_search(mode,recent,pool,pair_sets,rng,True)
    if not best:best=deterministic_search(mode,pool,pair_sets)
    if not best:
        raise RuntimeError(f'No valid 3x3 grid exists for {mode} using the current clue pool; this is a data/clue issue, not random exhaustion')
    q,rows,cols,ints,distinct,method=best
    med=statistics.median(ints)
    difficulty='Hard' if mode=='Deep Cut' or med<18 else ('Easy' if med>70 else 'Medium')
    return {'id':pid,'date':date.isoformat(),'mode':mode,'scope':mode,'difficulty':difficulty,'rows':[x['id'] for x in rows],'cols':[x['id'] for x in cols],'answerCounts':ints,'solutionPool':distinct,'qualityScore':round(q,2),'generationMethod':method}


def generate(games):
    all_puzzles=[];report_modes={};pid=1
    for mi,mode in enumerate(MODES):
        scoped_ids,counts,pool,pair_sets=build_index(games,mode)
        print(f'Generating {mode}: {len(scoped_ids)} scoped games, {len(pool)} usable clues')
        rng=random.Random(260817+mi*997);recent=[];d=START;mode_ps=[]
        while d<=END:
            p=build_mode_puzzle(mode,d,pid,recent,pool,pair_sets,rng);pid+=1
            mode_ps.append(p);recent=(recent+[tuple(p['rows']+p['cols'])])[-45:];d+=dt.timedelta(days=1)
        all_puzzles+=mode_ps
        medians=[statistics.median(p['answerCounts']) for p in mode_ps]
        methods={m:sum(p['generationMethod']==m for p in mode_ps) for m in {'quality-random','relaxed-random','deterministic-fallback'}}
        report_modes[mode]={'puzzles':len(mode_ps),'scopedGames':len(scoped_ids),'usableClues':len(pool),'medianAnswersPerSquare':round(statistics.median(medians),1),'minAnswers':min(min(p['answerCounts']) for p in mode_ps),'maxAnswers':max(max(p['answerCounts']) for p in mode_ps),'generationMethods':methods}
    all_puzzles.sort(key=lambda p:(p['date'],MODES.index(p['mode'])))
    return all_puzzles,report_modes


def main():
    games=base.build_games()
    if len(games)<4000:raise RuntimeError(f'Catalogue too small: {len(games)}')
    puzzles,mode_report=generate(games)
    clue_counts={s['id']:sum(base.match(g,s) for g in games) for s in base.CLUE_SPECS}
    out="window.GAMEGRID_DATA=(()=>{\nconst games="+json.dumps(games,separators=(',',':'),ensure_ascii=False)+";\n"+base.js_clues()+"\nconst puzzles="+json.dumps(puzzles,separators=(',',':'))+";\nreturn {games,clues,puzzles,meta:{gameCount:games.length,clueCount:clueSpecs.length,puzzleCount:puzzles.length,modes:"+json.dumps(MODES)+",source:'PlayMyData (IGDB-derived)',generated:new Date().toISOString()}};\n})();\n"
    open('data.js','w',encoding='utf-8').write(out)
    report={'games':len(games),'clues':len(base.CLUE_SPECS),'puzzles':len(puzzles),'modes':mode_report,'first':START.isoformat(),'last':END.isoformat(),'clueCounts':clue_counts}
    open('catalog-report.json','w').write(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
