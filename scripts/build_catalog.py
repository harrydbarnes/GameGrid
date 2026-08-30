#!/usr/bin/env python3
import ast,csv,datetime as dt,hashlib,io,json,math,random,re,sys,urllib.request

SOURCES=[
('Nintendo','https://raw.githubusercontent.com/riccardoRubei/MSR2024-Data-Showcase/main/final_dataset/all_games_Nintendo.csv'),
('PC','https://raw.githubusercontent.com/riccardoRubei/MSR2024-Data-Showcase/main/final_dataset/all_games_PC.csv'),
('PlayStation','https://raw.githubusercontent.com/riccardoRubei/MSR2024-Data-Showcase/main/final_dataset/all_games_PlayStation.csv'),
('Xbox','https://raw.githubusercontent.com/riccardoRubei/MSR2024-Data-Showcase/main/final_dataset/all_games_Xbox.csv')]
GENRES_URL='https://raw.githubusercontent.com/riccardoRubei/MSR2024-Data-Showcase/main/final_dataset/genres.csv'
PLATFORMS_URL='https://raw.githubusercontent.com/riccardoRubei/MSR2024-Data-Showcase/main/final_dataset/platforms.csv'
# Keep the whole upstream catalogue for source-quality checks and future puzzle
# generation. The former 6,000-record cut-off silently discarded well-known
# games with fewer ratings and made the search results depend on an opaque
# popularity ranking. The browser search index is reduced later to the audited
# union of scheduled puzzle answers.
MAX_GAMES=None
# This is the first day of the reset public schedule.  Keep it fixed so future
# catalogue rebuilds preserve the published puzzle numbering.
START=dt.date(2026,8,23)
END=dt.date(2026,12,31)

ALIASES={
'id':['id','game_id'],'title':['name','title'],'date':['first_release_date','release_date','released','date'],
'platforms':['platforms','platform_names'],'genres':['genres','genre_names'],'developers':['involved_companies','developers','developer'],
'publishers':['publishers','publisher'],'rating':['rating','total_rating'],'ratings_count':['rating_count','total_rating_count','ratings_count','review_count'],'people_polled':['people_polled']}
ALIASES['franchise']=['franchise','franchises','series','collection']

# The research snapshot is IGDB-derived but is not live: its latest records can
# lag recent releases.  These are deliberately limited to major, released games
# from the current era, so a snapshot lag cannot remove obvious player answers.
# They are merged with (rather than replace) the upstream data below.
# Their popularity fields are intentionally zero: an upstream record supplies
# its own rating when available, while an absent record must not gain invented
# rating-based puzzle eligibility or an artificial rarity rank.
ESSENTIAL_GAMES=[
 ('Gears of War',2006,['Xbox 360','PC'],['Epic Games'],['Microsoft Game Studios'],['Shooter','Adventure'],84,9000),
 ('BioShock',2007,['PC','Xbox 360','PlayStation 3'],['Irrational Games'],['2K'],['Shooter','Adventure'],88,11000),
 ('Mass Effect',2007,['Xbox 360','PC','PlayStation 3'],['BioWare'],['EA'],['Role-playing (RPG)','Adventure'],86,10000),
 ('Grand Theft Auto IV',2008,['PlayStation 3','Xbox 360','PC'],['Rockstar North'],['Rockstar Games'],['Adventure','Action'],92,18000),
 ('Demon’s Souls',2009,['PlayStation 3'],['FromSoftware'],['Sony Computer Entertainment'],['Role-playing (RPG)','Adventure'],89,8000),
 ('Death Stranding',2019,['PlayStation 4','PC'],['Kojima Productions'],['Sony Interactive Entertainment'],['Adventure','Action'],85,18000),
 ('Cyberpunk 2077',2020,['PC','PlayStation 4','PlayStation 5','Xbox One','Xbox Series'],['CD Projekt Red'],['CD Projekt'],['Role-playing (RPG)','Adventure'],76,30000),
 ('Ghost of Tsushima',2020,['PlayStation 4','PlayStation 5','PC'],['Sucker Punch Productions'],['Sony Interactive Entertainment'],['Adventure','Action'],83,15000),
 ('Marvel’s Spider-Man: Miles Morales',2020,['PlayStation 4','PlayStation 5','PC'],['Insomniac Games'],['Sony Interactive Entertainment'],['Adventure','Action'],85,9000),
 ('Hitman 3',2021,['PC','PlayStation 4','PlayStation 5','Xbox One','Xbox Series','Switch'],['IO Interactive'],['IO Interactive'],['Shooter','Adventure'],87,8000),
 ('It Takes Two',2021,['PC','PlayStation 4','PlayStation 5','Xbox One','Xbox Series','Switch'],['Hazelight Studios'],['EA'],['Adventure','Platform'],88,14000),
 ('Metroid Dread',2021,['Switch'],['MercurySteam','Nintendo EPD'],['Nintendo'],['Platform','Adventure'],88,8500),
 ('Ratchet & Clank: Rift Apart',2021,['PlayStation 5','PC'],['Insomniac Games'],['Sony Interactive Entertainment'],['Platform','Shooter'],88,7000),
 ('Returnal',2021,['PlayStation 5','PC'],['Housemarque'],['Sony Interactive Entertainment'],['Shooter','Adventure'],85,6500),
 ('Psychonauts 2',2021,['PC','PlayStation 4','Xbox One','Xbox Series'],['Double Fine'],['Xbox Game Studios'],['Platform','Adventure'],89,5000),
 ('Pokémon Legends: Arceus',2022,['Switch'],['Game Freak'],['Nintendo'],['Role-playing (RPG)','Adventure'],83,11000),
 ('Horizon Forbidden West',2022,['PlayStation 4','PlayStation 5','PC'],['Guerrilla Games'],['Sony Interactive Entertainment'],['Adventure','Role-playing (RPG)'],88,9500),
 ('Gran Turismo 7',2022,['PlayStation 4','PlayStation 5'],['Polyphony Digital'],['Sony Interactive Entertainment'],['Racing'],87,7500),
 ('Stray',2022,['PC','PlayStation 4','PlayStation 5','Xbox One','Xbox Series','Switch'],['BlueTwelve Studio'],['Annapurna Interactive'],['Adventure','Indie'],83,8500),
 ('Xenoblade Chronicles 3',2022,['Switch'],['Monolith Soft'],['Nintendo'],['Role-playing (RPG)','Adventure'],88,6000),
 ('Fire Emblem Engage',2023,['Switch'],['Intelligent Systems'],['Nintendo'],['Role-playing (RPG)','Strategy'],80,4500),
 ('Hi-Fi Rush',2023,['PC','Xbox Series','PlayStation 5'],['Tango Gameworks'],['Bethesda Softworks'],['Action','Rhythm'],87,6500),
 ('Super Mario Bros. Wonder',2023,['Switch'],['Nintendo EPD'],['Nintendo'],['Platform'],91,9000),
 ('Final Fantasy XVI',2023,['PlayStation 5','PC'],['Square Enix Creative Business Unit III'],['Square Enix'],['Role-playing (RPG)','Adventure'],87,9000),
 ('Armored Core VI: Fires of Rubicon',2023,['PC','PlayStation 4','PlayStation 5','Xbox One','Xbox Series'],['FromSoftware'],['Bandai Namco Entertainment'],['Action'],86,7500),
 ('Alan Wake 2',2023,['PC','PlayStation 5','Xbox Series'],['Remedy Entertainment'],['Epic Games Publishing'],['Adventure','Shooter'],89,7000),
 ('Baldur’s Gate 3',2023,['PC','PlayStation 5','Xbox Series'],['Larian Studios'],['Larian Studios'],['Role-playing (RPG)','Strategy'],96,25000),
 ('The Legend of Zelda: Tears of the Kingdom',2023,['Switch'],['Nintendo EPD'],['Nintendo'],['Adventure','Puzzle'],96,20000),
 ('Marvel’s Spider-Man 2',2023,['PlayStation 5','PC'],['Insomniac Games'],['Sony Interactive Entertainment'],['Adventure','Action'],90,10000),
 ('Like a Dragon: Infinite Wealth',2024,['PC','PlayStation 4','PlayStation 5','Xbox One','Xbox Series'],['Ryu Ga Gotoku Studio'],['Sega'],['Role-playing (RPG)','Adventure'],89,6000),
 ('Helldivers 2',2024,['PC','PlayStation 5'],['Arrowhead Game Studios'],['Sony Interactive Entertainment'],['Shooter'],82,14000),
 ('Final Fantasy VII Rebirth',2024,['PlayStation 5','PC'],['Square Enix Creative Business Unit I'],['Square Enix'],['Role-playing (RPG)','Adventure'],92,9000),
 ('Astro Bot',2024,['PlayStation 5'],['Team Asobi'],['Sony Interactive Entertainment'],['Platform'],94,8000),
 ('Indiana Jones and the Great Circle',2024,['PC','Xbox Series','PlayStation 5'],['MachineGames'],['Bethesda Softworks'],['Adventure','Action'],87,5000),
 ('Monster Hunter Wilds',2025,['PC','PlayStation 5','Xbox Series'],['Capcom'],['Capcom'],['Role-playing (RPG)','Adventure'],88,11000),
 ('Kingdom Come: Deliverance II',2025,['PC','PlayStation 5','Xbox Series'],['Warhorse Studios'],['Deep Silver'],['Role-playing (RPG)','Adventure'],88,5000),
 ('Clair Obscur: Expedition 33',2025,['PC','PlayStation 5','Xbox Series'],['Sandfall Interactive'],['Kepler Interactive'],['Role-playing (RPG)'],92,8500),
]

def pick(row,k):
    low={str(x).lower():x for x in row}
    for a in ALIASES[k]:
        if a in low:return row[low[a]]
    return ''

def parse_any(v,keep_numeric=False):
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
        if item and (keep_numeric or not item.isdigit()):out.append(item)
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
    try:
        n=float(v)
        return n if math.isfinite(n) else 0.0
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

def read_lookup(url,key,value):
    with urllib.request.urlopen(url,timeout=120) as r:data=r.read().decode('utf-8-sig','replace')
    return {str(row[key]).strip():str(row[value]).strip() for row in csv.DictReader(io.StringIO(data)) if row.get(key) and row.get(value)}

def build_games():
    # The four game files store IGDB genre and platform IDs, not names.  Keep
    # those IDs through parsing and resolve them through the source's own
    # lookup tables; otherwise nearly every source game loses its genre.
    genre_names=read_lookup(GENRES_URL,'genre_id','genre')
    platform_names=read_lookup(PLATFORMS_URL,'id','name')
    merged={}
    for group,url in SOURCES:
        for row in read_source(group,url):
            title=str(pick(row,'title') or '').strip()
            if not title:continue
            yr=year_of(pick(row,'date'))
            if yr<1975 or yr>dt.date.today().year+1:continue
            rawid=str(pick(row,'id') or '').strip()
            key=rawid or re.sub(r'[^a-z0-9]+','-',title.lower()).strip('-')
            plats=[norm_platform(platform_names.get(str(x),str(x))) for x in parse_any(pick(row,'platforms'),keep_numeric=True)]
            if not plats:plats=[group if group!='Nintendo' else 'Nintendo platform']
            genres=[genre_names.get(str(x),str(x)) for x in parse_any(pick(row,'genres'),keep_numeric=True)]
            devs=parse_any(pick(row,'developers'))
            pubs=parse_any(pick(row,'publishers'))
            franchises=parse_any(pick(row,'franchise'))
            r=num(pick(row,'rating'))
            # The source names its two participation signals review_count and
            # people_polled.  Either may be present, so retain the stronger
            # observed count as the static catalogue-popularity proxy.
            rc=max(num(pick(row,'ratings_count')),num(pick(row,'people_polled')))
            g=merged.get(key)
            if not g:g={'id':key,'title':title,'year':yr,'platforms':[],'developers':[],'publishers':[],'tags':[],'franchise':'','rating':round(r,1),'ratingsCount':int(rc)}
            g['platforms']=list(dict.fromkeys(g['platforms']+plats));g['tags']=list(dict.fromkeys(g['tags']+genres));g['developers']=list(dict.fromkeys(g['developers']+devs));g['publishers']=list(dict.fromkeys(g['publishers']+pubs));g['franchise']=g.get('franchise') or (franchises[0] if franchises else '');g['rating']=max(g['rating'],round(r,1));g['ratingsCount']=max(g['ratingsCount'],int(rc));merged[key]=g
    # Backfill major releases that post-date the fixed research snapshot.  Match
    # by normalised title and first-release year so the supplement enriches an
    # upstream record when it exists instead of creating a duplicate answer.
    def title_key(title,year):
        return (re.sub(r'[^a-z0-9]+','',title.lower().replace('’',"'")),year)
    by_title={title_key(g['title'],g['year']):key for key,g in merged.items()}
    for title,year,plats,devs,pubs,tags,rating,ratings_count in ESSENTIAL_GAMES:
        key=by_title.get(title_key(title,year))
        if key is None:
            key='essential-'+re.sub(r'[^a-z0-9]+','-',title.lower().replace('’',"'"))
            merged[key]={'id':key,'title':title,'year':year,'platforms':[],'developers':[],'publishers':[],'tags':[],'franchise':'','rating':0,'ratingsCount':0}
            by_title[title_key(title,year)]=key
        g=merged[key]
        g['platforms']=list(dict.fromkeys(g['platforms']+plats));g['tags']=list(dict.fromkeys(g['tags']+tags));g['developers']=list(dict.fromkeys(g['developers']+devs));g['publishers']=list(dict.fromkeys(g['publishers']+pubs));g['rating']=max(g['rating'],rating);g['ratingsCount']=max(g['ratingsCount'],ratings_count)
    games=list(merged.values())
    games.sort(key=lambda g:(g['ratingsCount'],g['rating'],g['year']),reverse=True)
    # MAX_GAMES remains an optional local-development escape hatch.  Production
    # leaves it unset to retain every eligible game from every source.
    chosen=games if MAX_GAMES is None else games[:MAX_GAMES]
    return sorted(chosen,key=lambda g:g['title'].lower())

CLUE_SPECS=[]
def add(cid,label,kind,value):CLUE_SPECS.append({'id':cid,'label':label,'kind':kind,'value':value})
for cid,label,val in [('pc','PC','PC'),('playstation','PlayStation platform','PlayStation'),('xbox','Xbox platform','Xbox'),('nintendo','Nintendo platform','Nintendo'),('switch','Nintendo Switch','Switch'),('switch2','Nintendo Switch 2','Switch 2'),('ps5','PlayStation 5','PlayStation 5'),('ps4','PlayStation 4','PlayStation 4'),('ps3','PlayStation 3','PlayStation 3'),('ps2','PlayStation 2','PlayStation 2'),('ps1','Original PlayStation','PlayStation'),('xseries','Xbox Series','Xbox Series'),('xone','Xbox One','Xbox One'),('x360','Xbox 360','Xbox 360'),('xboxoriginal','Original Xbox','Xbox'),('wiiu','Wii U','Wii U'),('wii','Wii','Wii'),('gamecube','GameCube','GameCube'),('n64','Nintendo 64','Nintendo 64'),('snes','SNES','SNES'),('nes','NES','NES'),('gba','Game Boy Advance','Game Boy Advance'),('gbc','Game Boy Color','Game Boy Color'),('gb','Game Boy','Game Boy'),('ds','Nintendo DS','Nintendo DS'),('3ds','Nintendo 3DS','Nintendo 3DS'),('dreamcast','Dreamcast','Dreamcast'),('megadrive','Mega Drive / Genesis','Mega Drive')]:add(cid,label,'platform',val)
for cid,label,platforms in [('gen6','Sixth-generation console',['PlayStation 2','GameCube','Xbox','Dreamcast']),('gen7','Seventh-generation console',['PlayStation 3','Xbox 360','Wii']),('gen8','Eighth-generation console',['PlayStation 4','Xbox One','Wii U','Switch']),('gen9','Ninth-generation console',['PlayStation 5','Xbox Series','Switch 2'])]:add(cid,label,'platformAny',platforms)
for cid,label,a,b in [('pre1990','Released before 1990',0,1989),('y1990s','Released in the 1990s',1990,1999),('y2000s','Released in the 2000s',2000,2009),('y2010s','Released in the 2010s',2010,2019),('y2020s','Released in the 2020s',2020,2029),('pre2000','Released before 2000',0,1999),('post2015','Released 2015 or later',2015,2099)]:add(cid,label,'yearRange',[a,b])
for cid,label,val in [('rpg','RPG','role-playing'),('shooter','Shooter','shooter'),('strategy','Strategy','strategy'),('racing','Racing','racing'),('sport','Sports','sport'),('fighting','Fighting','fighting'),('platformer','Platformer','platform'),('puzzle','Puzzle','puzzle'),('adventure','Adventure','adventure'),('simulation','Simulation','simulator'),('indie','Indie','indie'),('arcade','Arcade','arcade')]:add(cid,label,'genre',val)
for cid,label,n in [('rating70','Rating 65+ / 6.5+',65),('rating80','Rating 75+ / 7.5+',75),('rating85','Rating 80+ / 8+',80),('rating90','Rating 85+ / 8.5+',85)]:add(cid,label,'rating',n)
for cid,label,kind,val in [('oneword','One-word title','titleWords',1),('shorttitle','Title under 8 characters','titleLength',7),('numbertitle','Number in the title','titleRegex',r'\d'),('lettera','Title begins A–F','titleInitial','ABCDEF'),('letterg','Title begins G–L','titleInitial','GHIJKL'),('letterm','Title begins M–R','titleInitial','MNOPQR'),('letters','Title begins S–Z','titleInitial','STUVWXYZ')]:add(cid,label,kind,val)

def _maker_slug(value):
    slug=re.sub(r'[^a-z0-9]+','-',str(value).lower()).strip('-')
    return slug or hashlib.sha1(str(value).encode('utf-8')).hexdigest()[:10]


PUBLISHER_FAMILIES=(
    ('Nintendo',('nintendo',)),
    ('Sony',('sony',)),
    # Bethesda is included here because it is the same first-party Microsoft
    # family in the current source snapshot; this keeps the maker row useful
    # without pretending Bethesda is an independent platform ecosystem.
    ('Xbox / Microsoft',('microsoft','xbox','bethesda')),
    ('EA',('electronic arts',)),
    ('Square Enix',('square enix',)),
    ('Rockstar',('rockstar',)),
    ('Bethesda',('bethesda',)),
    ('Capcom',('capcom',)),
    ('Ubisoft',('ubisoft',)),
    ('Bandai Namco',('bandai namco',)),
)


def publisher_family(value):
    folded=str(value or '').casefold()
    for family,needles in PUBLISHER_FAMILIES:
        if any(needle in folded for needle in needles):return family
    return ''


# The upstream snapshot occasionally omits involved-company metadata for an
# otherwise well-known title. Keep small, reviewed corrections in the browser
# bootstrap so Trial does not reject an answer for a missing source field. Do
# not feed these aliases back into puzzle generation: published answer counts
# must remain stable when the source snapshot is refreshed.
KNOWN_PUBLISHER_ALIASES={
    'the last of us part ii': ('Sony Interactive Entertainment',),
}


def known_publisher_aliases(game):
    title=re.sub(r'[^a-z0-9]+',' ',str(game.get('title','')).casefold()).strip()
    return list(KNOWN_PUBLISHER_ALIASES.get(title,()))


def trial_specs(games,min_games=3):
    """Build stable maker criteria for Trial from usable catalogue metadata.

    Three is the hard lower bound for a valid square, so a maker with fewer
    releases cannot contribute a playable Trial row.
    """
    groups={}
    displays={}
    fields=(
        ('developer','developers','Made by'),
        ('publisher','publishers','Published by'),
        ('publisherFamily','publishers','Published by'),
        ('franchise','franchise','Franchise'),
    )
    for game in games:
        game_id=game.get('id')
        if game_id is None:continue
        for kind,key,prefix in fields:
            values=game.get(key,[]) if key!='franchise' else [game.get(key)]
            if not isinstance(values,(list,tuple)):values=[values]
            for raw in values:
                value=str(raw or '').strip()
                if kind=='publisherFamily':value=publisher_family(value)
                if len(value)<2 or value.isdigit():continue
                group_key=(kind,value.casefold())
                groups.setdefault(group_key,set()).add(game_id)
                displays.setdefault(group_key,value)
    specs=[]
    for (kind,folded),ids in sorted(groups.items(),key=lambda item:(item[0][0],item[0][1])):
        if len(ids)<min_games:continue
        value=displays[(kind,folded)]
        prefix=next(prefix for candidate,key,prefix in fields if candidate==kind)
        specs.append({'id':f'{kind}:{_maker_slug(value)}','label':f'{prefix} {value}','kind':kind,'value':value,'family':'maker'})
    return specs


def match(g,s):
    k=s['kind'];v=s['value']
    if k=='developer':return v in g.get('developers',[])
    if k=='publisher':return v in g.get('publishers',[])
    if k=='publisherFamily':return any(publisher_family(value)==v for value in g.get('publishers',[]))
    if k=='franchise':return g.get('franchise','')==v
    if k=='platform':
        if v=='PlayStation':return any(p.startswith('PlayStation') or p in {'PSP','PS Vita'} for p in g['platforms'])
        if v=='Xbox':return any(p.startswith('Xbox') for p in g['platforms'])
        if v=='Nintendo':return any(p in {'Switch','Switch 2','Wii U','Wii','GameCube','Nintendo 64','SNES','NES','Game Boy Advance','Game Boy Color','Game Boy','Nintendo DS','Nintendo 3DS','Nintendo platform'} for p in g['platforms'])
        return v in g['platforms']
    if k=='platformAny':return any(p in v for p in g['platforms'])
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
    return f"const clueSpecs={specs};\nconst clues=Object.fromEntries(clueSpecs.map(s=>[s.id,{{label:s.label,test:g=>{{const k=s.kind,v=s.value;if(k==='platform'){{if(v==='PlayStation')return g.platforms.some(p=>p.startsWith('PlayStation')||['PSP','PS Vita'].includes(p));if(v==='Xbox')return g.platforms.some(p=>p.startsWith('Xbox'));if(v==='Nintendo')return g.platforms.some(p=>['Switch','Switch 2','Wii U','Wii','GameCube','Nintendo 64','SNES','NES','Game Boy Advance','Game Boy Color','Game Boy','Nintendo DS','Nintendo 3DS','Nintendo platform'].includes(p));return g.platforms.includes(v)}}if(k==='platformAny')return g.platforms.some(p=>v.includes(p));if(k==='yearRange')return g.year>=v[0]&&g.year<=v[1];if(k==='genre')return g.tags.some(t=>String(t).toLowerCase().includes(v));if(k==='rating'){{let r=g.rating||0;if(r&&r<=10)r*=10;return r>=v}}if(k==='titleWords')return (g.title.match(/[A-Za-z0-9]+/g)||[]).length===v;if(k==='titleLength')return g.title.replace(/\\W/g,'').length<=v;if(k==='titleRegex')return new RegExp(v).test(g.title);if(k==='titleInitial')return v.includes(g.title.slice(0,1).toUpperCase());return false}}}}]));"

def js_clues(specs=None):
    """Serialize fixed and dynamic criteria into the browser matcher."""
    specs=CLUE_SPECS if specs is None else specs
    literal=json.dumps(specs,separators=(',',':'),ensure_ascii=False)
    return (
        'const clueSpecs='+literal+';\n'
        "const clues=Object.fromEntries(clueSpecs.map(s=>[s.id,{label:s.label,test:g=>{const k=s.kind,v=s.value;"
        "if(k==='developer')return (g.developers||[]).includes(v);"
        "if(k==='publisher')return (g.publishers||[]).includes(v);"
        "if(k==='publisherFamily'){const q=value=>String(value||'').toLowerCase();const family=value=>{const folded=q(value);if(folded.includes('nintendo'))return 'Nintendo';if(folded.includes('sony'))return 'Sony';if(folded.includes('microsoft')||folded.includes('xbox')||folded.includes('bethesda'))return 'Xbox / Microsoft';if(folded.includes('electronic arts'))return 'EA';if(folded.includes('square enix'))return 'Square Enix';if(folded.includes('rockstar'))return 'Rockstar';if(folded.includes('capcom'))return 'Capcom';if(folded.includes('ubisoft'))return 'Ubisoft';if(folded.includes('bandai namco'))return 'Bandai Namco';return ''};const publishers=[...(g.publishers||[]),...(g.publisherAliases||[])];return publishers.some(p=>family(p)===v)}"
        "if(k==='franchise')return String(g.franchise||'')===v;"
        "if(k==='platform'){if(v==='PlayStation')return (g.platforms||[]).some(p=>p.startsWith('PlayStation')||['PSP','PS Vita'].includes(p));if(v==='Xbox')return (g.platforms||[]).some(p=>p.startsWith('Xbox'));if(v==='Nintendo')return (g.platforms||[]).some(p=>['Switch','Switch 2','Wii U','Wii','GameCube','Nintendo 64','SNES','NES','Game Boy Advance','Game Boy Color','Game Boy','Nintendo DS','Nintendo 3DS','Nintendo platform'].includes(p));return (g.platforms||[]).includes(v)}"
        "if(k==='platformAny')return (g.platforms||[]).some(p=>v.includes(p));"
        "if(k==='yearRange')return g.year>=v[0]&&g.year<=v[1];"
        "if(k==='genre')return (g.tags||[]).some(t=>String(t).toLowerCase().includes(v));"
        "if(k==='rating'){let r=g.rating||0;if(r&&r<=10)r*=10;return r>=v}"
        "if(k==='titleWords')return (g.title.match(/[A-Za-z0-9]+/g)||[]).length===v;"
        "if(k==='titleLength')return g.title.replace(/\\W/g,'').length<=v;"
        "if(k==='titleRegex')return new RegExp(v).test(g.title);"
        "if(k==='titleInitial')return v.includes(g.title.slice(0,1).toUpperCase());"
        'return false}}]));'
    )


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
