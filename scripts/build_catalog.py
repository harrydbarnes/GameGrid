#!/usr/bin/env python3
import ast,csv,datetime as dt,hashlib,io,json,random,re,sys,urllib.request

SOURCES=[
('Nintendo','https://raw.githubusercontent.com/riccardoRubei/MSR2024-Data-Showcase/main/final_dataset/all_games_Nintendo.csv'),
('PC','https://raw.githubusercontent.com/riccardoRubei/MSR2024-Data-Showcase/main/final_dataset/all_games_PC.csv'),
('PlayStation','https://raw.githubusercontent.com/riccardoRubei/MSR2024-Data-Showcase/main/final_dataset/all_games_PlayStation.csv'),
('Xbox','https://raw.githubusercontent.com/riccardoRubei/MSR2024-Data-Showcase/main/final_dataset/all_games_Xbox.csv')]
MAX_GAMES=6000
START=dt.date(2026,8,17)
END=dt.date(2026,12,31)

ALIASES={
'id':['id','game_id'],'title':['name','title'],'date':['first_release_date','release_date','released','date'],
'platforms':['platforms','platform_names'],'genres':['genres','genre_names'],'developers':['involved_companies','developers','developer'],
'publishers':['publishers','publisher'],'rating':['rating','total_rating'],'ratings_count':['rating_count','total_rating_count','ratings_count']}

def pick(row,k):
    low={str(x).lower():x for x in row}
    for a in ALIASES[k]:
        if a in low:return row[low[a]]
    return ''

def parse_any(v):
    if v is None:return []
    if isinstance(v,(list,tuple)):return list(v)
    s=str(v).strip()
    if not s or s.lower() in {'nan','none','null'}:return []
    try:x=json.loads(s)
    except Exception:
        try:x=ast.literal_eval(s)
        except Exception:x=[p.strip() for p in re.split(r'[|;,]',s) if p.strip()]
    if not isinstance(x,(list,tuple)):x=[x]
    out=[]
    for item in x:
        if isinstance(item,dict):
            item=item.get('name') or item.get('company',{}).get('name') or item.get('platform',{}).get('name') or ''
        elif isinstance(item,(list,tuple)) and item:item=item[-1]
        item=str(item).strip(" []{}'\"")
        if item and not item.isdigit():out.append(item)
    return list(dict.fromkeys(out))

def year_of(v):
    s=str(v or '')
    m=re.search(r'(19|20)\d{2}',s)
    if m:return int(m.group())
    try:
        n=float(s)
        if n>100000000:return dt.datetime.utcfromtimestamp(n).year
    except:pass
    return 0

def num(v):
    try:return float(v)
    except:return 0.0

def norm_platform(p):
    q=p.lower()
    rules=[('playstation 5','PlayStation 5'),('playstation 4','PlayStation 4'),('playstation 3','PlayStation 3'),('playstation 2','PlayStation 2'),('playstation vita','PS Vita'),('playstation portable','PSP'),('ps vita','PS Vita'),('psp','PSP'),('playstation','PlayStation'),('xbox series','Xbox Series'),('xbox one','Xbox One'),('xbox 360','Xbox 360'),('xbox','Xbox'),('switch 2','Switch 2'),('nintendo switch','Switch'),('wii u','Wii U'),('wii','Wii'),('gamecube','GameCube'),('nintendo 64','Nintendo 64'),('super nintendo','SNES'),('snes','SNES'),('nintendo entertainment system','NES'),('nes','NES'),('game boy advance','Game Boy Advance'),('game boy color','Game Boy Color'),('game boy','Game Boy'),('nintendo 3ds','Nintendo 3DS'),('nintendo ds','Nintendo DS'),('dreamcast','Dreamcast'),('mega drive','Mega Drive'),('genesis','Mega Drive'),('windows','PC'),('linux','PC'),('mac','PC'),('pc','PC')]
    for a,b in rules:
        if a in q:return b
    return p.strip()

def read_source(group,url):
    print('Downloading',group,file=sys.stderr)
    with urllib.request.urlopen(url,timeout=120) as r:data=r.read().decode('utf-8-sig','replace')
    return list(csv.DictReader(io.StringIO(data)))

def build_games():
    merged={}
    for group,url in SOURCES:
        for row in read_source(group,url):
            title=str(pick(row,'title') or '').strip()
            if not title:continue
            yr=year_of(pick(row,'date'))
            if yr<1975 or yr>dt.date.today().year+1:continue
            rawid=str(pick(row,'id') or '').strip()
            key=rawid or re.sub(r'[^a-z0-9]+','-',title.lower()).strip('-')
            plats=[norm_platform(x) for x in parse_any(pick(row,'platforms'))]
            if not plats:plats=[group if group!='Nintendo' else 'Nintendo platform']
            genres=parse_any(pick(row,'genres'))
            devs=parse_any(pick(row,'developers'))
            pubs=parse_any(pick(row,'publishers'))
            r=num(pick(row,'rating')); rc=num(pick(row,'ratings_count'))
            g=merged.get(key)
            if not g:g={'id':key,'title':title,'year':yr,'platforms':[],'developers':[],'publishers':[],'tags':[],'franchise':'','rating':round(r,1),'ratingsCount':int(rc)}
            g['platforms']=list(dict.fromkeys(g['platforms']+plats));g['tags']=list(dict.fromkeys(g['tags']+genres));g['developers']=list(dict.fromkeys(g['developers']+devs));g['publishers']=list(dict.fromkeys(g['publishers']+pubs));g['rating']=max(g['rating'],round(r,1));g['ratingsCount']=max(g['ratingsCount'],int(rc));merged[key]=g
    games=list(merged.values())
    games.sort(key=lambda g:(g['ratingsCount'],g['rating'],g['year']),reverse=True)
    # keep quality/popularity while ensuring every era survives
    chosen=[];seen=set()
    for decade in [1980,1990,2000,2010,2020]:
        for g in [x for x in games if decade<=x['year']<decade+10][:500]:
            if g['id'] not in seen:chosen.append(g);seen.add(g['id'])
    for g in games:
        if len(chosen)>=MAX_GAMES:break
        if g['id'] not in seen:chosen.append(g);seen.add(g['id'])
    chosen.sort(key=lambda g:g['title'].lower())
    return chosen[:MAX_GAMES]

CLUE_SPECS=[]
def add(cid,label,kind,value):CLUE_SPECS.append({'id':cid,'label':label,'kind':kind,'value':value})
for cid,label,val in [('pc','PC','PC'),('playstation','PlayStation platform','PlayStation'),('xbox','Xbox platform','Xbox'),('nintendo','Nintendo platform','Nintendo'),('switch','Nintendo Switch','Switch'),('switch2','Nintendo Switch 2','Switch 2'),('ps5','PlayStation 5','PlayStation 5'),('ps4','PlayStation 4','PlayStation 4'),('ps3','PlayStation 3','PlayStation 3'),('ps2','PlayStation 2','PlayStation 2'),('ps1','Original PlayStation','PlayStation'),('xseries','Xbox Series','Xbox Series'),('xone','Xbox One','Xbox One'),('x360','Xbox 360','Xbox 360'),('xboxoriginal','Original Xbox','Xbox'),('wiiu','Wii U','Wii U'),('wii','Wii','Wii'),('gamecube','GameCube','GameCube'),('n64','Nintendo 64','Nintendo 64'),('snes','SNES','SNES'),('nes','NES','NES'),('gba','Game Boy Advance','Game Boy Advance'),('gbc','Game Boy Color','Game Boy Color'),('gb','Game Boy','Game Boy'),('ds','Nintendo DS','Nintendo DS'),('3ds','Nintendo 3DS','Nintendo 3DS'),('dreamcast','Dreamcast','Dreamcast'),('megadrive','Mega Drive / Genesis','Mega Drive')]:add(cid,label,'platform',val)
for cid,label,a,b in [('pre1990','Released before 1990',0,1989),('y1990s','Released in the 1990s',1990,1999),('y2000s','Released in the 2000s',2000,2009),('y2010s','Released in the 2010s',2010,2019),('y2020s','Released in the 2020s',2020,2029),('pre2000','Released before 2000',0,1999),('post2015','Released 2015 or later',2015,2099)]:add(cid,label,'yearRange',[a,b])
for cid,label,val in [('rpg','RPG','role-playing'),('shooter','Shooter','shooter'),('strategy','Strategy','strategy'),('racing','Racing','racing'),('sport','Sports','sport'),('fighting','Fighting','fighting'),('platformer','Platformer','platform'),('puzzle','Puzzle','puzzle'),('adventure','Adventure','adventure'),('simulation','Simulation','simulator'),('indie','Indie','indie'),('arcade','Arcade','arcade')]:add(cid,label,'genre',val)
for cid,label,n in [('rating70','Rating 70+ / 7+',70),('rating80','Rating 80+ / 8+',80),('rating85','Rating 85+ / 8.5+',85),('rating90','Rating 90+ / 9+',90)]:add(cid,label,'rating',n)
for cid,label,kind,val in [('oneword','One-word title','titleWords',1),('shorttitle','Title under 8 characters','titleLength',7),('numbertitle','Number in the title','titleRegex',r'\d'),('lettera','Title begins A–F','titleInitial','ABCDEF'),('letterg','Title begins G–L','titleInitial','GHIJKL'),('letterm','Title begins M–R','titleInitial','MNOPQR'),('letters','Title begins S–Z','titleInitial','STUVWXYZ')]:add(cid,label,kind,val)


def match(g,s):
    k=s['kind'];v=s['value']
    if k=='platform':
        if v=='PlayStation':return any(p.startswith('PlayStation') or p in {'PSP','PS Vita'} for p in g['platforms'])
        if v=='Xbox':return any(p.startswith('Xbox') for p in g['platforms'])
        if v=='Nintendo':return any(p in {'Switch','Switch 2','Wii U','Wii','GameCube','Nintendo 64','SNES','NES','Game Boy Advance','Game Boy Color','Game Boy','Nintendo DS','Nintendo 3DS','Nintendo platform'} for p in g['platforms'])
        return v in g['platforms']
    if k=='yearRange':return v[0]<=g['year']<=v[1]
    if k=='genre':return any(v in str(t).lower() for t in g['tags'])
    if k=='rating':
        r=g.get('rating',0);r=r*10 if r and r<=10 else r
        return r>=v
    if k=='titleWords':return len(re.findall(r"[A-Za-z0-9]+",g['title']))==v
    if k=='titleLength':return len(re.sub(r'\W','',g['title']))<=v
    if k=='titleRegex':return bool(re.search(v,g['title']))
    if k=='titleInitial':return g['title'][:1].upper() in v
    return False

def generate_puzzles(games):
    counts={s['id']:sum(match(g,s) for g in games) for s in CLUE_SPECS}
    eligible=[s for s in CLUE_SPECS if 25<=counts[s['id']]<=4500]
    rng=random.Random(260817);puzzles=[];d=START;pid=1;recent=[]
    while d<=END:
        found=None
        for _ in range(20000):
            six=rng.sample(eligible,6);rows=six[:3];cols=six[3:]
            if any(x['kind']==y['kind'] and x['value']==y['value'] for x in rows for y in cols):continue
            intersections=[]
            for r in rows:
                for c in cols:intersections.append(sum(match(g,r) and match(g,c) for g in games))
            if min(intersections)<3 or max(intersections)>800:continue
            score=sum(intersections)
            sig=tuple(x['id'] for x in six)
            if sig in recent:continue
            found=(rows,cols,intersections,score);break
        if not found:raise RuntimeError('Could not generate valid puzzle for '+str(d))
        rows,cols,ints,_=found
        puzzles.append({'id':pid,'date':d.isoformat(),'mode':'Classic','rows':[x['id'] for x in rows],'cols':[x['id'] for x in cols],'answerCounts':ints})
        recent=(recent+[tuple(x['id'] for x in rows+cols)])[-30:]
        pid+=1;d+=dt.timedelta(days=1)
    return puzzles,counts

def js_clues():
    specs=json.dumps(CLUE_SPECS,separators=(',',':'),ensure_ascii=False)
    return f"const clueSpecs={specs};\nconst clues=Object.fromEntries(clueSpecs.map(s=>[s.id,{{label:s.label,test:g=>{{const k=s.kind,v=s.value;if(k==='platform'){{if(v==='PlayStation')return g.platforms.some(p=>p.startsWith('PlayStation')||['PSP','PS Vita'].includes(p));if(v==='Xbox')return g.platforms.some(p=>p.startsWith('Xbox'));if(v==='Nintendo')return g.platforms.some(p=>['Switch','Switch 2','Wii U','Wii','GameCube','Nintendo 64','SNES','NES','Game Boy Advance','Game Boy Color','Game Boy','Nintendo DS','Nintendo 3DS','Nintendo platform'].includes(p));return g.platforms.includes(v)}}if(k==='yearRange')return g.year>=v[0]&&g.year<=v[1];if(k==='genre')return g.tags.some(t=>String(t).toLowerCase().includes(v));if(k==='rating'){{let r=g.rating||0;if(r&&r<=10)r*=10;return r>=v}}if(k==='titleWords')return (g.title.match(/[A-Za-z0-9]+/g)||[]).length===v;if(k==='titleLength')return g.title.replace(/\\W/g,'').length<=v;if(k==='titleRegex')return new RegExp(v).test(g.title);if(k==='titleInitial')return v.includes(g.title.slice(0,1).toUpperCase());return false}}}}]));"

def main():
    games=build_games();puzzles,counts=generate_puzzles(games)
    if len(games)<4000:raise RuntimeError(f'Catalogue too small: {len(games)}')
    if len(CLUE_SPECS)<40:raise RuntimeError('Not enough clue types')
    out="window.GAMEGRID_DATA=(()=>{\nconst games="+json.dumps(games,separators=(',',':'),ensure_ascii=False)+";\n"+js_clues()+"\nconst puzzles="+json.dumps(puzzles,separators=(',',':'))+";\nreturn {games,clues,puzzles,meta:{gameCount:games.length,clueCount:clueSpecs.length,puzzleCount:puzzles.length,source:'PlayMyData (IGDB-derived)',generated:new Date().toISOString()}};\n})();\n"
    open('data.js','w',encoding='utf-8').write(out)
    report={'games':len(games),'clues':len(CLUE_SPECS),'puzzles':len(puzzles),'first':puzzles[0]['date'],'last':puzzles[-1]['date'],'clueCounts':counts}
    open('catalog-report.json','w').write(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
