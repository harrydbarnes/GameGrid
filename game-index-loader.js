(() => {
  const data = window.GAMEGRID_DATA;
  const manifest = window.GAMEGRID_CATALOG_MANIFEST;
  const validAsset = (value, prefix) => typeof value === 'string' && new RegExp(`^${prefix}\\.[a-f0-9]{16}\\.js$`).test(value);
  let worker = null;
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
      Object.assign(existing, game);
      // A later worker search must not erase rich fields merged by the
      // deferred details loader. The compact index deliberately carries only
      // empty developer/publisher placeholders.
      if (Array.isArray(developers) && developers.length) existing.developers = developers;
      if (Array.isArray(publishers) && publishers.length) existing.publishers = publishers;
      return existing;
    }
    data.games.push(game);
    return game;
  }

  function fail(error) {
    const reason = error instanceof Error ? error : new Error('Game search is unavailable');
    pending.forEach(request => request.reject(reason));
    pending.clear();
    worker?.terminate();
    worker = null;
    readyPromise = null;
    throw reason;
  }

  function ensure() {
    if (readyPromise) return readyPromise;
    if (typeof Worker === 'undefined' || !validAsset(manifest?.indexAsset, 'index') || !validAsset(manifest?.searchAsset, 'search')) {
      return Promise.reject(new Error('Game search is unavailable'));
    }
    let resolveReady;
    let rejectReady;
    readyPromise = new Promise((resolve, reject) => { resolveReady = resolve; rejectReady = reject; });
    try {
      worker = new Worker(`./${manifest.searchAsset}`);
      worker.onmessage = event => {
        const message = event.data || {};
        if (message.type === 'ready') {
          resolveReady(message.count || 0);
          document.dispatchEvent(new CustomEvent('gamegrid:index-ready', { detail: { count: message.count || 0 } }));
          return;
        }
        if (message.type !== 'results') return;
        const request = pending.get(message.id);
        if (!request) return;
        pending.delete(message.id);
        request.resolve((message.rows || []).map(merge).filter(Boolean));
      };
      worker.onerror = error => {
        const reason = error instanceof Error ? error : new Error('Game search is unavailable');
        rejectReady(reason);
        try { fail(reason); } catch {}
      };
    } catch (error) {
      readyPromise = null;
      return Promise.reject(error);
    }
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
  document.addEventListener('click', event => {
    if (event.target.closest?.('#grid .cell.empty')) ensure().catch(() => {});
  });
})();
