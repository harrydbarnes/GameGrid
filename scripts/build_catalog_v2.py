#!/usr/bin/env python3
import datetime as dt, json, random, statistics
import build_catalog as base

START=base.START
END=base.END
MODES=['Classic','Retro','Nintendo','PlayStation','Xbox','Deep Cut']

NINTENDO={'Switch','Switch 2','Wii U','Wii','GameCube','Nintendo 64','SNES','NES','Game Boy Advance','Game Boy Color','Game Boy','Nintendo DS','Nintendo 3DS','Nintendo platform'}

def scope_ok(g,mode):
    if mode=='Classic' or mode=='Deep Cut': return True
    if mode=='Retro': return g['year']<=2009
    if mode=='Nintendo': return any(p in NINTENDO for p in g['platforms'])
    if mode=='PlayStation': return any(p.startswith('PlayStation') or p in {'PSP','PS Vita'} for p in g['platforms'])
    if mode=='Xbox': return any(p.startswith('Xbox') for p in g['platforms'])
    return True

def clue_pool(mode, counts):
    specs=[s for s in base.CLUE_SPECS if 20<=counts.get(s['id'],0)<=5000]
    if mode=='Classic': return specs
    if mode=='Retro':
        excluded={'y2020s','post2015','switch2','ps5','ps4','xseries','xone'}
        return [s for s in specs if s['id'] not in excluded]
    if mode=='Nintendo':
        platform_ids={'switch','switch2','wiiu','wii','gamecube','n64','snes','nes','gba','gbc','gb','ds','3ds'}
        generic={'y1990s','y2000s','y2010s','y2020s','pre2000','rpg','shooter','strategy','racing','sport','fighting','platformer','puzzle','adventure','simulation','indie','arcade','oneword','numbertitle','lettera','letterg','letterm','letters','rating70','rating80','rating85'}
        return [s for s in specs if s['id'] in platform_ids|generic]
    if mode=='PlayStation':
        platform_ids={'ps1','ps2','ps3','ps4','ps5'}
        generic={'y1990s','y2000s','y2010s','y2020s','pre2000','post2015','rpg','shooter','strategy','racing','sport','fighting','platformer','puzzle','adventure','simulation','indie','arcade','oneword','numbertitle','lettera','letterg','letterm','letters','rating70','rating80','rating85','rating90'}
        return [s for s in specs if s['id'] in platform_ids|generic]
    if mode=='Xbox':
        platform_ids={'xboxoriginal','x360','xone','xseries'}
        generic={'y2000s','y2010s','y2020s','post2015','rpg','shooter','strategy','racing','sport','fighting','platformer','puzzle','adventure','simulation','indie','arcade','oneword','numbertitle','lettera','letterg','letterm','letters','rating70','rating80','rating85','rating90'}
        return [s for s in specs if s['id'] in platform_ids|generic]
    if mode=='Deep Cut':
        return [s for s in specs if s['id'] not in {'pc','playstation','xbox','nintendo','rating70'}]
    return specs

def intersection_games(games,r,c,mode):
    return [g for g in games if scope_ok(g,mode) and base.match(g,r) and base.match(g,c)]

def quality(ints, mode):
    if not ints:return None
    low,high=(5,300)
    if mode=='Deep Cut': low,high=3,45
    elif mode in {'Nintendo','PlayStation','Xbox','Retro'}: low,high=4,180
    if min(ints)<low or max(ints)>high:return None
    med=statistics.median(ints)
    spread=max(ints)-min(ints)
    target=18 if mode=='Deep Cut' else 45
    # reward a mix of tighter and broader squares without wild outliers
    return abs(med-target)+(spread*0.08)

def build_mode_puzzle(games, mode, date, pid, recent, clue_counts, rng):
    pool=clue_pool(mode,clue_counts)
    best=None
    for _ in range(12000):
        six=rng.sample(pool,6);rows=six[:3];cols=six[3:]
        ids=[s['id'] for s in six]
        if len(set(ids))<6:continue
        # Avoid row/column pairs that are effectively the same category.
        if any(r['kind']==c['kind'] and r['value']==c['value'] for r in rows for c in cols):continue
        sig=tuple(ids)
        if sig in recent:continue
        cells=[];ints=[]
        for r in rows:
            for c in cols:
                gs=intersection_games(games,r,c,mode);ints.append(len(gs));cells.append(gs)
        q=quality(ints,mode)
        if q is None:continue
        # Require enough distinct solution titles across the full board.
        distinct=len({g['id'] for cell in cells for g in cell})
        if distinct<30 and mode!='Deep Cut':continue
        if distinct<18:continue
        # Avoid puzzles where one game can solve too many cells.
        frequency={}
        for cell in cells:
            for g in cell:frequency[g['id']]=frequency.get(g['id'],0)+1
        if frequency and max(frequency.values())>3:continue
        if best is None or q<best[0]:best=(q,rows,cols,ints,distinct)
        if q<8:break
    if not best:raise RuntimeError(f'Could not build {mode} puzzle for {date}')
    q,rows,cols,ints,distinct=best
    difficulty='Hard' if mode=='Deep Cut' or statistics.median(ints)<18 else ('Easy' if statistics.median(ints)>70 else 'Medium')
    return {'id':pid,'date':date.isoformat(),'mode':mode,'scope':mode,'difficulty':difficulty,'rows':[x['id'] for x in rows],'cols':[x['id'] for x in cols],'answerCounts':ints,'solutionPool':distinct,'qualityScore':round(q,2)}

def generate(games):
    # Counts are scope-aware for pool eligibility.
    all_puzzles=[];report_modes={};pid=1
    for mi,mode in enumerate(MODES):
        scoped=[g for g in games if scope_ok(g,mode)]
        counts={s['id']:sum(base.match(g,s) for g in scoped) for s in base.CLUE_SPECS}
        rng=random.Random(260817+mi*997);recent=[];d=START;mode_ps=[]
        while d<=END:
            p=build_mode_puzzle(games,mode,d,pid,recent,counts,rng);pid+=1
            mode_ps.append(p);recent=(recent+[tuple(p['rows']+p['cols'])])[-45:];d+=dt.timedelta(days=1)
        all_puzzles+=mode_ps
        medians=[statistics.median(p['answerCounts']) for p in mode_ps]
        report_modes[mode]={'puzzles':len(mode_ps),'scopedGames':len(scoped),'medianAnswersPerSquare':round(statistics.median(medians),1),'minAnswers':min(min(p['answerCounts']) for p in mode_ps),'maxAnswers':max(max(p['answerCounts']) for p in mode_ps)}
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
