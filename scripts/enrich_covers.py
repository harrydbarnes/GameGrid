#!/usr/bin/env python3
"""Enrich generated GameGrid data.js with IGDB cover URLs at build time.
Requires free IGDB/Twitch credentials in IGDB_CLIENT_ID and IGDB_CLIENT_SECRET.
No credentials are ever shipped to the browser. Missing credentials simply skip enrichment.
"""
import json, os, re, sys, time, urllib.parse, urllib.request

CLIENT_ID=os.getenv('IGDB_CLIENT_ID','').strip()
CLIENT_SECRET=os.getenv('IGDB_CLIENT_SECRET','').strip()
ROOT=os.path.join(os.path.dirname(__file__),'..')
MANIFEST=os.path.join(ROOT,'catalog-manifest.js')

if not CLIENT_ID or not CLIENT_SECRET:
    print('IGDB credentials not configured; cover enrichment skipped.')
    sys.exit(0)

def post(url,data,headers=None):
    req=urllib.request.Request(url,data=data.encode(),headers=headers or {},method='POST')
    with urllib.request.urlopen(req,timeout=60) as r:return json.loads(r.read().decode())

token=post('https://id.twitch.tv/oauth2/token?'+urllib.parse.urlencode({'client_id':CLIENT_ID,'client_secret':CLIENT_SECRET,'grant_type':'client_credentials'}),'').get('access_token')
if not token:raise RuntimeError('Could not obtain IGDB access token')
headers={'Client-ID':CLIENT_ID,'Authorization':'Bearer '+token,'Accept':'application/json','Content-Type':'text/plain'}

manifest=open(MANIFEST,encoding='utf-8').read()
match=re.search(r'window\.GAMEGRID_CATALOG_MANIFEST=(\{.*\});',manifest)
if not match:raise RuntimeError('Could not locate generated catalogue manifest')
DATA=os.path.join(ROOT,json.loads(match.group(1))['dataAsset'])
text=open(DATA,encoding='utf-8').read()
m=re.search(r'const games=(\[.*?\]);\nconst clueSpecs=',text,re.S)
if not m:raise RuntimeError('Could not locate generated games array')
games=json.loads(m.group(1))
ids=[]
for g in games:
    try: ids.append(int(g['id']))
    except: pass

covers={}
# IGDB accepts batches. Fetch cover image IDs for catalogue IDs, respecting the free API rate limit.
for pos in range(0,len(ids),500):
    batch=ids[pos:pos+500]
    body='fields id,cover.image_id; where id = ('+','.join(map(str,batch))+'); limit 500;'
    rows=post('https://api.igdb.com/v4/games',body,headers)
    for row in rows:
        image=(row.get('cover') or {}).get('image_id')
        if image:covers[str(row['id'])]=image
    time.sleep(.28)

for g in games:
    image=covers.get(str(g['id']))
    if image:
        # t_cover_big is portrait-oriented and large enough for grid/search while remaining CDN optimised.
        g['coverUrl']='https://images.igdb.com/igdb/image/upload/t_cover_big/'+image+'.jpg'

new_games=json.dumps(games,separators=(',',':'),ensure_ascii=False)
text=text[:m.start(1)]+new_games+text[m.end(1):]
open(DATA,'w',encoding='utf-8').write(text)
print(f'Added real IGDB artwork to {len(covers)} of {len(games)} games.')
