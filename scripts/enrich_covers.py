#!/usr/bin/env python3
"""Enrich generated GameGrid details with IGDB cover URLs.

The lookup cache is a union of known cover IDs and checked IDs without a
cover. The Actions workflow keys each saved snapshot by catalogHash, while
restore-keys let a new catalogue reuse the previous snapshot and query only
new game IDs.
"""
import json, os, re, sys, time, urllib.parse, urllib.request
from pathlib import Path

from build_catalog_v3 import asset_sizes


CACHE_VERSION = 1
ROOT = os.path.join(os.path.dirname(__file__), '..')
MANIFEST = os.path.join(ROOT, 'catalog-manifest.js')
REPORT = os.path.join(ROOT, 'catalog-report.json')


def empty_cover_cache():
    return {'version': CACHE_VERSION, 'catalogHash': '', 'covers': {}, 'checked': []}


def load_cover_cache(path):
    """Load a validated cache, returning an empty cache for stale/malformed data."""
    try:
        payload = json.loads(Path(path).read_text(encoding='utf-8'))
    except (OSError, ValueError, TypeError):
        return empty_cover_cache()
    if not isinstance(payload, dict) or payload.get('version') != CACHE_VERSION:
        return empty_cover_cache()
    raw_covers = payload.get('covers')
    raw_checked = payload.get('checked')
    if not isinstance(raw_covers, dict) or not isinstance(raw_checked, list):
        return empty_cover_cache()
    covers = {str(key): value for key, value in raw_covers.items() if isinstance(value, str) and value}
    checked = {str(value) for value in raw_checked if value is not None}
    checked.update(covers)
    return {
        'version': CACHE_VERSION,
        'catalogHash': str(payload.get('catalogHash') or ''),
        'covers': covers,
        'checked': sorted(checked),
    }


def save_cover_cache(path, catalog_hash, covers, checked):
    """Atomically persist the cover map so an interrupted build cannot corrupt it."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        'version': CACHE_VERSION,
        'catalogHash': str(catalog_hash),
        'covers': {str(key): value for key, value in covers.items() if isinstance(value, str) and value},
        'checked': sorted({str(value) for value in checked}),
    }
    temporary = target.with_name(f'{target.name}.{os.getpid()}.tmp')
    temporary.write_text(json.dumps(payload, separators=(',', ':'), ensure_ascii=False), encoding='utf-8')
    os.replace(temporary, target)


def missing_cover_ids(ids, cache):
    """Return only IDs absent from both the positive and negative cache."""
    covers = cache.get('covers', {}) if isinstance(cache, dict) else {}
    checked = set(cache.get('checked', [])) if isinstance(cache, dict) else set()
    known = checked | {str(key) for key in covers}
    return [value for value in ids if str(value) not in known]


def set_output(name, value):
    output = os.getenv('GITHUB_OUTPUT')
    if not output:
        return
    with open(output, 'a', encoding='utf-8') as handle:
        handle.write(f'{name}={value}\n')


def post(url, data, headers=None):
    request = urllib.request.Request(url, data=data.encode(), headers=headers or {}, method='POST')
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.loads(response.read().decode())


def enrich():
    client_id = os.getenv('IGDB_CLIENT_ID', '').strip()
    client_secret = os.getenv('IGDB_CLIENT_SECRET', '').strip()
    if not client_id or not client_secret:
        print('IGDB credentials not configured; cover enrichment skipped.')
        set_output('cache-updated', 'false')
        return 0

    token = post('https://id.twitch.tv/oauth2/token?' + urllib.parse.urlencode({
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'client_credentials',
    }), '').get('access_token')
    if not token:
        raise RuntimeError('Could not obtain IGDB access token')
    headers = {
        'Client-ID': client_id,
        'Authorization': 'Bearer ' + token,
        'Accept': 'application/json',
        'Content-Type': 'text/plain',
    }

    manifest_text = Path(MANIFEST).read_text(encoding='utf-8')
    manifest_match = re.search(r'window\.GAMEGRID_CATALOG_MANIFEST=(\{.*\});', manifest_text)
    if not manifest_match:
        raise RuntimeError('Could not locate generated catalogue manifest')
    assets = json.loads(manifest_match.group(1))
    catalog_hash = assets.get('catalogHash')
    if not isinstance(catalog_hash, str) or not catalog_hash:
        raise RuntimeError('Generated catalogue manifest is missing catalogHash')

    index_path = os.path.join(ROOT, assets['indexAsset'])
    details_path = os.path.join(ROOT, assets['detailsAsset'])
    index_text = Path(index_path).read_text(encoding='utf-8')
    index_match = re.search(r'(?:window|globalThis)\.GAMEGRID_INDEX=(\[.*\]);', index_text, re.S)
    if not index_match:
        raise RuntimeError('Could not locate generated compact search index')
    games = [{'id': row[0]} for row in json.loads(index_match.group(1))]
    ids = []
    for game in games:
        try:
            ids.append(int(game['id']))
        except (TypeError, ValueError):
            pass

    details_text = Path(details_path).read_text(encoding='utf-8')
    details_match = re.search(r'window\.GAMEGRID_DETAILS=(\{.*\});', details_text, re.S)
    if not details_match:
        raise RuntimeError('Could not locate generated deferred-details payload')
    details = json.loads(details_match.group(1))

    cache_path = os.getenv('IGDB_COVER_CACHE_FILE', '').strip() or os.path.join(ROOT, '.cache', 'igdb-covers', 'cover-map.json')
    cache = load_cover_cache(cache_path)
    covers = dict(cache['covers'])
    checked = set(cache['checked']) | set(covers)
    missing = missing_cover_ids(ids, cache)
    queried = 0
    if missing:
        for position in range(0, len(missing), 500):
            batch = missing[position:position + 500]
            body = 'fields id,cover.image_id; where id = (' + ','.join(map(str, batch)) + '); limit 500;'
            rows = post('https://api.igdb.com/v4/games', body, headers)
            checked.update(str(value) for value in batch)
            for row in rows:
                image = (row.get('cover') or {}).get('image_id')
                if image:
                    covers[str(row['id'])] = image
            queried += len(batch)
            if position + 500 < len(missing):
                time.sleep(.28)

    for game in games:
        image = covers.get(str(game['id']))
        if image:
            # t_cover_big is portrait-oriented and large enough for grid/search
            # while remaining CDN-optimised.
            details['games'].setdefault(game['id'], {})['coverUrl'] = 'https://images.igdb.com/igdb/image/upload/t_cover_big/' + image + '.jpg'

    new_details = json.dumps(details, separators=(',', ':'), ensure_ascii=False)
    Path(details_path).write_text(details_text[:details_match.start(1)] + new_details + details_text[details_match.end(1):], encoding='utf-8')
    save_cover_cache(cache_path, catalog_hash, covers, checked)
    set_output('cache-updated', 'true')
    if os.path.exists(REPORT):
        report = json.loads(Path(REPORT).read_text(encoding='utf-8'))
        report['assetSizes'] = asset_sizes(assets, ROOT)
        Path(REPORT).write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(f'Added real IGDB artwork to {len(covers)} of {len(games)} games; queried {queried} new IDs and reused {len(ids) - queried} cached IDs.')
    return 0


if __name__ == '__main__':
    sys.exit(enrich())
