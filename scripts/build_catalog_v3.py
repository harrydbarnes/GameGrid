#!/usr/bin/env python3
import datetime as dt, json, random, statistics
import build_catalog as base
import build_catalog_v2 as v2

START=base.START
END=base.END
MODES=v2.MODES


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
    clue_counts={s['id']:sum(base.match(g,s) for g in games) for s in base.CLUE_SPECS}
    out="window.GAMEGRID_DATA=(()=>{\nconst games="+json.dumps(games,separators=(',',':'),ensure_ascii=False)+";\n"+base.js_clues()+"\nconst puzzles="+json.dumps(puzzles,separators=(',',':'))+";\nreturn {games,clues,puzzles,meta:{gameCount:games.length,clueCount:clueSpecs.length,puzzleCount:puzzles.length,modes:"+json.dumps(MODES)+",source:'PlayMyData (IGDB-derived)',generated:new Date().toISOString()}};\n})();\n"
    open('data.js','w',encoding='utf-8').write(out)
    report={'games':len(games),'clues':len(base.CLUE_SPECS),'puzzles':len(puzzles),'modes':mode_report,'first':START.isoformat(),'last':END.isoformat(),'clueCounts':clue_counts,'selection':'all eligible source records (no popularity cap)','essentialBackfill':len(base.ESSENTIAL_GAMES)}
    open('catalog-report.json','w').write(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
