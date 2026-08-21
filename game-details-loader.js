(() => {
  const MAX_RETRIES = 1;
  let loading = false;
  let announced = false;
  let unavailable = false;

  function announceUnavailable(reason, attempts) {
    if (unavailable) return;
    unavailable = true;
    document.dispatchEvent(new CustomEvent('gamegrid:details-unavailable', {
      detail: { reason, attempts },
    }));
  }

  function merge() {
    const details = window.GAMEGRID_DETAILS, data = window.GAMEGRID_DATA, manifest = window.GAMEGRID_CATALOG_MANIFEST;
    if (!details || !data || details.catalogHash !== manifest?.catalogHash || details.buildHash !== manifest?.buildHash) return false;
    const byId = new Map(data.games.map(game => [game.id, game]));
    let count = 0;
    Object.entries(details.games || {}).forEach(([id, detail]) => {
      const game = byId.get(id);
      if (!game || !detail || typeof detail !== 'object') return;
      Object.assign(game, detail);
      count++;
    });
    if (!announced) {
      announced = true;
      document.dispatchEvent(new CustomEvent('gamegrid:details-ready', { detail: { count } }));
    }
    return true;
  }

  function append(asset, retry) {
    loading = true;
    const script = document.createElement('script');
    script.src = `./${asset}${retry ? `?details-retry=${retry}` : ''}`;
    const retryOrFail = reason => {
      loading = false;
      if (retry < MAX_RETRIES) {
        append(asset, retry + 1);
        return;
      }
      announceUnavailable(reason, retry + 1);
    };
    script.onload = () => {
      if (merge()) {
        loading = false;
        return;
      }
      retryOrFail('stale');
    };
    script.onerror = () => retryOrFail('load');
    document.head.append(script);
  }

  function load() {
    if (unavailable) return false;
    if (window.GAMEGRID_DETAILS && merge()) return true;
    if (loading) return false;
    const asset = window.GAMEGRID_CATALOG_MANIFEST?.detailsAsset;
    if (!/^details\.[a-f0-9]{16}\.js$/.test(asset || '')) {
      announceUnavailable('missing', 0);
      return false;
    }
    append(asset, 0);
    return true;
  }

  window.GameGridDetails = {
    load,
    merge,
    get unavailable() { return unavailable; },
  };

  document.addEventListener('click', event => {
    if (event.target.closest('.result,.cell.solved,.answer-cell,.valid-answer')) load();
  });
})();
