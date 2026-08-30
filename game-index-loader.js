(() => {
  const data = window.GAMEGRID_DATA;
  const manifest = window.GAMEGRID_CATALOG_MANIFEST;
  const CACHE_NAME = 'gamegrid-search-index-v1';
  const validAsset = (value, prefix) => typeof value === 'string' && new RegExp(`^${prefix}\\.[a-f0-9]{16}\\.js$`).test(value);
  let worker = null;
  let workerUrl = null;
  let readyPromise = null;
  let nextRequest = 0;
  const pending = new Map();

  function asGame(row) {
    if (!Array.isArray(row) || row.length < 7) return null;
    const [id, title, year, platforms, tags, rating, ratingsCount] = row;
    if (id == null || typeof title !== 'string' || !Array.isArray(platforms) || !Array.isArray(tags)) return null;
    return { id, title, year, platforms, tags, rating, ratingsCount, developers: [], publishers: [] };
  }

  function merge(row) {
    const game = asGame(row);
    if (!game || !data?.games) return null;
    const existing = data.games.find(item => item.id === game.id);
    if (existing) {
      const developers = existing.developers;
      const publishers = existing.publishers;
      const publisherAliases = existing.publisherAliases;
      Object.assign(existing, game);
      // The compact index deliberately carries empty rich fields. Preserve any
      // developer or publisher data merged by the deferred details loader.
      if (Array.isArray(developers) && developers.length) existing.developers = developers;
      if (Array.isArray(publishers) && publishers.length) existing.publishers = publishers;
      if (Array.isArray(publisherAliases) && publisherAliases.length) existing.publisherAliases = publisherAliases;
      return existing;
    }
    data.games.push(game);
    return game;
  }

  function releaseWorker() {
    worker?.terminate();
    worker = null;
    if (workerUrl) URL.revokeObjectURL(workerUrl);
    workerUrl = null;
  }

  function fail(error) {
    const reason = error instanceof Error ? error : new Error('Game search is unavailable');
    pending.forEach(request => request.reject(reason));
    pending.clear();
    releaseWorker();
    readyPromise = null;
    return reason;
  }

  async function cachedText(asset) {
    const url = new URL(`./${asset}`, window.location.href).href;
    if (!('caches' in window)) {
      const response = await fetch(url);
      if (!response.ok) throw new Error(`Could not load ${asset}`);
      return response.text();
    }

    const cache = await caches.open(CACHE_NAME);
    let response = await cache.match(url);
    if (!response) {
      response = await fetch(url, { cache: 'no-store' });
      if (!response.ok) throw new Error(`Could not load ${asset}`);
      await cache.put(url, response.clone());
    }
    return response.text();
  }

  async function pruneCachedAssets() {
    if (!('caches' in window)) return;
    const cache = await caches.open(CACHE_NAME);
    const keep = new Set([
      new URL(`./${manifest.indexAsset}`, window.location.href).href,
      new URL(`./${manifest.searchAsset}`, window.location.href).href,
    ]);
    const keys = await cache.keys();
    await Promise.all(keys.filter(request => !keep.has(request.url) && /\/(?:index|search)\.[a-f0-9]{16}\.js$/.test(request.url)).map(request => cache.delete(request)));
  }

  async function createWorker() {
    // Cache Storage is not visible to importScripts. Build a same-origin blob
    // worker from the cached index and worker source so repeat visits avoid
    // downloading the large fingerprinted index again.
    if (!('caches' in window)) return new Worker(`./${manifest.searchAsset}`);
    const [indexSource, searchSource] = await Promise.all([
      cachedText(manifest.indexAsset),
      cachedText(manifest.searchAsset),
    ]);
    pruneCachedAssets().catch(() => {});
    const source = `${indexSource}\n${searchSource.replace('importScripts(INDEX_ASSET);', '')}`;
    workerUrl = URL.createObjectURL(new Blob([source], { type: 'text/javascript' }));
    return new Worker(workerUrl);
  }

  function ensure() {
    if (readyPromise) return readyPromise;
    if (typeof Worker === 'undefined' || !validAsset(manifest?.indexAsset, 'index') || !validAsset(manifest?.searchAsset, 'search')) {
      return Promise.reject(new Error('Game search is unavailable'));
    }
    readyPromise = new Promise((resolve, reject) => {
      createWorker().then(nextWorker => {
        worker = nextWorker;
        worker.onmessage = event => {
          const message = event.data || {};
          if (message.type === 'ready') {
            resolve(message.count || 0);
            document.dispatchEvent(new CustomEvent('gamegrid:index-ready', { detail: { count: message.count || 0 } }));
            return;
          }
          if (message.type !== 'results') return;
          const request = pending.get(message.id);
          if (!request) return;
          pending.delete(message.id);
          request.resolve((message.rows || []).map(merge).filter(Boolean));
        };
        worker.onerror = error => reject(fail(error));
      }).catch(error => reject(fail(error)));
    });
    return readyPromise;
  }

  function query(value, excluded = []) {
    return ensure().then(() => new Promise((resolve, reject) => {
      if (!worker) return reject(new Error('Game search is unavailable'));
      const id = ++nextRequest;
      pending.set(id, { resolve, reject });
      worker.postMessage({ type: 'search', id, query: String(value || ''), excluded: Array.isArray(excluded) ? excluded : [] });
    }));
  }

  window.GameGridSearch = { ensure, query, ready: () => Boolean(worker && readyPromise) };

  // The search index is the curated union of games used by the scheduled
  // intersections. Start it after the game has painted, rather than on the
  // first cell tap, so opening the answer sheet remains responsive on mobile.
  function warmInBackground() {
    const warm = () => ensure().catch(() => {});
    if ('requestIdleCallback' in window) window.requestIdleCallback(warm, { timeout: 3000 });
    else if (typeof window.setTimeout === 'function') window.setTimeout(warm, 900);
    else if (typeof setTimeout === 'function') setTimeout(warm, 900);
  }

  if (document.readyState === 'complete') warmInBackground();
  else if (typeof window.addEventListener === 'function') window.addEventListener('load', warmInBackground, { once: true });
  else if (typeof setTimeout === 'function') setTimeout(warmInBackground, 900);
})();
