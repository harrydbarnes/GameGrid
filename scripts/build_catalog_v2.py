#!/usr/bin/env python3
import datetime as dt, itertools, json, random, statistics
import build_catalog as base

START=base.START
END=base.END
MODES=['Classic','Retro','Modern','Nintendo','PlayStation','Xbox','Deep Cut','Trial']
NINTENDO={'Switch','Switch 2','Wii U','Wii','GameCube','Nintendo 64','SNES','NES','Game Boy Advance','Game Boy Color','Game Boy','Nintendo DS','Nintendo 3DS','Nintendo platform'}


def scope_ok(g,mode):
    if mode in {'Classic','Deep Cut'}: return True
    # The PS2 era began in 2000. The two era modes are deliberately exclusive.
    if mode=='Retro': return g['year']<=1999
    if mode=='Modern': return g['year']>=2000
    if mode=='Nintendo': return any(p in NINTENDO for p in g['platforms'])
    if mode=='PlayStation': return any(p.startswith('PlayStation') or p in {'PSP','PS Vita'} for p in g['platforms'])
    if mode=='Xbox': return any(p.startswith('Xbox') for p in g['platforms'])
    return True


def specs_for_mode(games,mode):
    return base.CLUE_SPECS+base.trial_specs(games) if mode=='Trial' else base.CLUE_SPECS


def all_clue_specs(games):
    return base.CLUE_SPECS+base.trial_specs(games)


def clue_pool(mode,counts,scoped_games=None,specs=None):
    # A criterion should not be rejected solely because the source catalogue
    # grew.  The former fixed 5,000 ceiling was appropriate for a 6,000-game
    # sample but removed normal platform/genre clues from the complete index.
    scoped=scoped_games if scoped_games is not None else max(counts.values(),default=0)
    ceiling=max(5000,int(scoped*.95))
    specs=specs or base.CLUE_SPECS
    specs=[s for s in specs if 20<=counts.get(s['id'],0)<=ceiling or (mode=='Trial' and clue_family(s)=='maker' and counts.get(s['id'],0)>=6)]
    if mode=='Classic': return specs
    if mode=='Retro':
        excluded={'y2000s','y2010s','y2020s','post2015','switch2','ps5','ps4','xseries','xone'}
        return [s for s in specs if s['id'] not in excluded]
    if mode=='Modern':
        excluded={'pre1990','y1990s','pre2000','ps1','n64','snes','nes','gba','gbc','gb','ds','3ds','dreamcast','megadrive'}
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
    if mode=='Trial':
        return [s for s in specs if clue_family(s)=='maker' or clue_family(s) in {'platform','genre','era','rating','title'}]
    return specs


def clue_family(spec):
    kind=spec.get('kind','')
    if kind in {'developer','publisher','franchise'}: return 'maker'
    if kind=='platform': return 'platform'
    if kind=='yearRange': return 'release'
    if kind=='genre': return 'genre'
    if kind=='rating': return 'rating'
    if kind.startswith('title'): return 'title'
    return kind or 'other'


def family_signature(specs):
    return tuple(sorted(clue_family(s) for s in specs))


def variety_ok(rows,cols,mode):
    six=list(rows)+list(cols)
    fams=[clue_family(s) for s in six]
    counts={f:fams.count(f) for f in set(fams)}
    # Every grid should mix at least three kinds of knowledge rather than becoming
    # six versions of years/platforms/etc. The themed modes may use three platform
    # criteria, but no family may dominate a standard grid with four or more.
    min_families=3
    max_one_family=3 if mode in {'Nintendo','PlayStation','Xbox'} else 2
    if len(counts)<min_families:return False
    if max(counts.values())>max_one_family:return False
    # Each axis must itself contain some variety. This prevents, for example,
    # three release decades across the top crossed with three consoles down the side.
    if len({clue_family(s) for s in rows})<2:return False
    if len({clue_family(s) for s in cols})<2:return False
    return True


def schedule_ok(specs,recent_puzzles):
    ids={s['id'] for s in specs}
    sig=family_signature(specs)
    # The six criteria are the puzzle's identity. Sharing 4/6 would be 66.7%, so
    # cap all of the previous seven scheduled grids at three shared criteria (50%).
    for age,p in enumerate(reversed(recent_puzzles[-7:]),start=1):
        previous=set(p['rows']+p['cols'])
        if len(ids & previous)>3:return False
        # Do not repeat the exact same family recipe on consecutive/nearby days.
        if age<=3 and sig==tuple(p.get('familySignature',())):return False
    return True


def repetition_penalty(specs,recent_puzzles):
    """Softly favour criteria that have not appeared much in the last fortnight."""
    if not recent_puzzles:return 0
    freq={}
    for p in recent_puzzles[-14:]:
        for cid in p['rows']+p['cols']:freq[cid]=freq.get(cid,0)+1
    return sum(freq.get(s['id'],0) for s in specs)*1.8


def bounds(mode,relaxed=False):
    if mode=='Deep Cut': return (3,80 if relaxed else 45)
    if mode in {'Nintendo','PlayStation','Xbox','Retro','Modern'}: return (3 if relaxed else 4,320 if relaxed else 180)
    return (3 if relaxed else 5,500 if relaxed else 300)


def quality(ints,mode,relaxed=False):
    if not ints:return None
    low,high=bounds(mode,relaxed)
    if min(ints)<low or max(ints)>high:return None
    med=statistics.median(ints);spread=max(ints)-min(ints);target=18 if mode=='Deep Cut' else 45
    return abs(med-target)+(spread*0.08)


def build_index(games,mode,specs=None):
    scoped_ids={i for i,g in enumerate(games) if scope_ok(g,mode)}
    specs=specs or specs_for_mode(games,mode)
    clue_sets={spec['id']:{i for i in scoped_ids if base.match(games[i],spec)} for spec in specs}
    counts={cid:len(ids) for cid,ids in clue_sets.items()}
    pool=clue_pool(mode,counts,len(scoped_ids),specs)
    pair_sets={}
    if mode=='Trial':
        # Trial fixes makers on the row axis and facts on the column axis, so
        # maker×maker and fact×fact intersections can never be used. Avoiding
        # those combinations keeps the dynamic maker index linear in the
        # number of maker criteria instead of quadratic.
        candidates=((a,b) for a in pool for b in pool if clue_family(a)=='maker' and clue_family(b)!='maker')
    else:
        candidates=itertools.combinations(pool,2)
    for a,b in candidates:
        pair_sets[tuple(sorted((a['id'],b['id'])))]=clue_sets[a['id']] & clue_sets[b['id']]
    return scoped_ids,counts,pool,pair_sets


def pair_lookup(pair_sets,a,b):
    return pair_sets.get(tuple(sorted((a,b))),set())


def structurally_ok(rows,cols,mode):
    if len({x['id'] for x in rows+cols})<6:return False
    if not variety_ok(rows,cols,mode):return False
    return not any(r['kind']==c['kind'] and r['value']==c['value'] for r in rows for c in cols)


def evaluate(rows,cols,pair_sets,mode,recent_puzzles,relaxed=False,allow_reuse=False):
    six=list(rows)+list(cols)
    if not structurally_ok(rows,cols,mode):return None
    if not schedule_ok(six,recent_puzzles):return None
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
    q+=repetition_penalty(six,recent_puzzles)
    return q,ints,distinct


def random_search(mode,recent_puzzles,pool,pair_sets,rng,relaxed=False):
    best=None
    attempts=3500 if not relaxed else 5500
    for _ in range(attempts):
        six=rng.sample(pool,6);rows=six[:3];cols=six[3:]
        ev=evaluate(rows,cols,pair_sets,mode,recent_puzzles,relaxed=relaxed,allow_reuse=relaxed)
        if not ev:continue
        q,ints,distinct=ev
        if best is None or q<best[0]:best=(q,rows,cols,ints,distinct,'relaxed-random' if relaxed else 'quality-random')
        if q<(18 if relaxed else 10):break
    return best


def deterministic_search(mode,pool,pair_sets,recent_puzzles):
    """Find a scheduled-valid K3,3 arrangement deterministically if RNG misses one."""
    low,high=bounds(mode,True);target=18 if mode=='Deep Cut' else 45
    neighbours={s['id']:[] for s in pool};by_id={s['id']:s for s in pool}
    for a,b in itertools.combinations(pool,2):
        n=len(pair_lookup(pair_sets,a['id'],b['id']))
        if low<=n<=high:
            neighbours[a['id']].append((b['id'],n));neighbours[b['id']].append((a['id'],n))
    row_candidates=sorted(pool,key=lambda s:len(neighbours[s['id']]),reverse=True)
    best=None
    for rows in itertools.combinations(row_candidates,3):
        common=set(x[0] for x in neighbours[rows[0]['id']])
        common&=set(x[0] for x in neighbours[rows[1]['id']]);common&=set(x[0] for x in neighbours[rows[2]['id']]);common-={r['id'] for r in rows}
        cols=[by_id[cid] for cid in common if cid in by_id]
        if len(cols)<3:continue
        def col_score(c):return sum(abs(len(pair_lookup(pair_sets,r['id'],c['id']))-target) for r in rows)
        cols=sorted(cols,key=col_score)[:20]
        for chosen in itertools.combinations(cols,3):
            six=list(rows)+list(chosen)
            if not structurally_ok(list(rows),list(chosen),mode) or not schedule_ok(six,recent_puzzles):continue
            cells=[pair_lookup(pair_sets,r['id'],c['id']) for r in rows for c in chosen];ints=[len(x) for x in cells]
            if min(ints)<3:continue
            distinct=len(set().union(*cells))
            if distinct<9:continue
            med=statistics.median(ints);spread=max(ints)-min(ints)
            q=abs(med-target)+(spread*0.08)+25+repetition_penalty(six,recent_puzzles)
            cand=(q,list(rows),list(chosen),ints,distinct,'deterministic-fallback')
            if best is None or q<best[0]:best=cand
            if q<42:return best
    return best


def build_mode_puzzle(mode,date,pid,recent_puzzles,pool,pair_sets,rng):
    best=random_search(mode,recent_puzzles,pool,pair_sets,rng,False)
    if not best:best=random_search(mode,recent_puzzles,pool,pair_sets,rng,True)
    if not best:best=deterministic_search(mode,pool,pair_sets,recent_puzzles)
    if not best:raise RuntimeError(f'No varied, schedule-safe 3x3 grid exists for {mode} on {date}')
    q,rows,cols,ints,distinct,method=best
    med=statistics.median(ints);difficulty='Hard' if mode=='Deep Cut' or med<18 else ('Easy' if med>70 else 'Medium')
    sig=family_signature(rows+cols)
    previous=recent_puzzles[-1] if recent_puzzles else None
    shared_previous=len(set([x['id'] for x in rows+cols]) & set(previous['rows']+previous['cols'])) if previous else 0
    return {'id':pid,'date':date.isoformat(),'mode':mode,'scope':mode,'difficulty':difficulty,'rows':[x['id'] for x in rows],'cols':[x['id'] for x in cols],'answerCounts':ints,'solutionPool':distinct,'qualityScore':round(q,2),'generationMethod':method,'familySignature':list(sig),'sharedWithPrevious':shared_previous}


def generate(games):
    all_puzzles=[];report_modes={};pid=1
    for mi,mode in enumerate(MODES):
        scoped_ids,counts,pool,pair_sets=build_index(games,mode)
        print(f'Generating {mode}: {len(scoped_ids)} scoped games, {len(pool)} usable criteria')
        rng=random.Random(260817+mi*997);d=START;mode_ps=[]
        while d<=END:
            p=build_mode_puzzle(mode,d,pid,mode_ps,pool,pair_sets,rng);pid+=1
            mode_ps.append(p);d+=dt.timedelta(days=1)
        # Schedule assertions: neighbouring grids may overlap, but never by more than 3/6 criteria.
        for i,p in enumerate(mode_ps):
            for prev in mode_ps[max(0,i-7):i]:
                shared=len(set(p['rows']+p['cols']) & set(prev['rows']+prev['cols']))
                if shared>3:raise RuntimeError(f'{mode} schedule repetition: {p["date"]} shares {shared}/6 criteria with {prev["date"]}')
            if len(set(p['familySignature']))<3:raise RuntimeError(f'{mode} variety failure on {p["date"]}')
        all_puzzles+=mode_ps
        medians=[statistics.median(p['answerCounts']) for p in mode_ps]
        methods={m:sum(p['generationMethod']==m for p in mode_ps) for m in {'quality-random','relaxed-random','deterministic-fallback'}}
        shares=[p['sharedWithPrevious'] for p in mode_ps[1:]]
        report_modes[mode]={'puzzles':len(mode_ps),'scopedGames':len(scoped_ids),'usableCriteria':len(pool),'medianAnswersPerSquare':round(statistics.median(medians),1),'minAnswers':min(min(p['answerCounts']) for p in mode_ps),'maxAnswers':max(max(p['answerCounts']) for p in mode_ps),'generationMethods':methods,'maxAdjacentSharedCriteria':max(shares) if shares else 0,'avgAdjacentSharedCriteria':round(statistics.mean(shares),2) if shares else 0}
    all_puzzles.sort(key=lambda p:(p['date'],MODES.index(p['mode'])))
    return all_puzzles,report_modes


def main():
    games=base.build_games()
    if len(games)<4000:raise RuntimeError(f'Catalogue too small: {len(games)}')
    puzzles,mode_report=generate(games)
    clue_counts={s['id']:sum(base.match(g,s) for g in games) for s in base.CLUE_SPECS}
    out="window.GAMEGRID_DATA=(()=>{\nconst games="+json.dumps(games,separators=(',',':'),ensure_ascii=False)+";\n"+base.js_clues()+"\nconst puzzles="+json.dumps(puzzles,separators=(',',':'))+";\nreturn {games,clues,puzzles,meta:{gameCount:games.length,clueCount:clueSpecs.length,puzzleCount:puzzles.length,modes:"+json.dumps(MODES)+",source:'PlayMyData (IGDB-derived)',generated:new Date().toISOString()}};\n})();\n"
    open('data.js','w',encoding='utf-8').write(out)
    report={'games':len(games),'criteria':len(base.CLUE_SPECS),'puzzles':len(puzzles),'modes':mode_report,'first':START.isoformat(),'last':END.isoformat(),'criterionCounts':clue_counts}
    open('catalog-report.json','w').write(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
