#!/usr/bin/env python3
import datetime as dt, json, random, statistics
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


def quality(ints,mode):
    if not ints:return None
    low,high=(5,300)
    if mode=='Deep Cut': low,high=3,45
    elif mode in {'Nintendo','PlayStation','Xbox','Retro'}: low,high=4,180
    if min(ints)<low or max(ints)>high:return None
    med=statistics.median(ints);spread=max(ints)-min(ints);target=18 if mode=='Deep Cut' else 45
    return abs(med-target)+(spread*0.08)


def build_index(games,mode):
    scoped_ids={i for i,g in enumerate(games) if scope_ok(g,mode)}
    clue_sets={}
    for spec in base.CLUE_SPECS:
        clue_sets[spec['id']]={i for i in scoped_ids if base.match(games[i],spec)}
    counts={cid:len(ids) for cid,ids in clue_sets.items()}
    pool=clue_pool(mode,counts)
    pair_sets={}
    for a in pool:
        for b in pool:
            if a['id']>=b['id']:continue
            pair_sets[(a['id'],b['id'])]=clue_sets[a['id']] & clue_sets[b['id']]
    return scoped_ids,counts,pool,pair_sets


def pair_lookup(pair_sets,a,b):
    return pair_sets.get((a,b) if a<b else (b,a),set())


def build_mode_puzzle(mode,date,pid,recent,pool,pair_sets,rng):
    best=None
    attempts=1800
    for _ in range(attempts):
        six=rng.sample(pool,6);rows=six[:3];cols=six[3:]
        ids=[s['id'] for s in six]
        if tuple(ids) in recent:continue
        if any(r['kind']==c['kind'] and r['value']==c['value'] for r in rows for c in cols):continue
        cells=[pair_lookup(pair_sets,r['id'],c['id']) for r in rows for c in cols]
        ints=[len(x) for x in cells]
        q=quality(ints,mode)
        if q is None:continue
        union=set().union(*cells)
        distinct=len(union)
        if distinct<(18 if mode=='Deep Cut' else 30):continue
        frequency={}
        too_reusable=False
        for cell in cells:
            for gid in cell:
                n=frequency.get(gid,0)+1;frequency[gid]=n
                if n>3:
                    too_reusable=True;break
            if too_reusable:break
        if too_reusable:continue
        if best is None or q<best[0]:best=(q,rows,cols,ints,distinct)
        if q<8:break
    if not best:raise RuntimeError(f'Could not build {mode} puzzle for {date}')
    q,rows,cols,ints,distinct=best
    med=statistics.median(ints)
    difficulty='Hard' if mode=='Deep Cut' or med<18 else ('Easy' if med>70 else 'Medium')
    return {'id':pid,'date':date.isoformat(),'mode':mode,'scope':mode,'difficulty':difficulty,'rows':[x['id'] for x in rows],'cols':[x['id'] for x in cols],'answerCounts':ints,'solutionPool':distinct,'qualityScore':round(q,2)}


def generate(games):
    all_puzzles=[];report_modes={};pid=1
    for mi,mode in enumerate(MODES):
        scoped_ids,counts,pool,pair_sets=build_index(games,mode)
        rng=random.Random(260817+mi*997);recent=[];d=START;mode_ps=[]
        while d<=END:
            p=build_mode_puzzle(mode,d,pid,recent,pool,pair_sets,rng);pid+=1
            mode_ps.append(p);recent=(recent+[tuple(p['rows']+p['cols'])])[-45:];d+=dt.timedelta(days=1)
        all_puzzles+=mode_ps
        medians=[statistics.median(p['answerCounts']) for p in mode_ps]
        report_modes[mode]={'puzzles':len(mode_ps),'scopedGames':len(scoped_ids),'medianAnswersPerSquare':round(statistics.median(medians),1),'minAnswers':min(min(p['answerCounts']) for p in mode_ps),'maxAnswers':max(max(p['answerCounts']) for p in mode_ps)}
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
