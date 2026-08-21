(() => {
  let loading = false;
  let announced = false;
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
  function load() {
    if (window.GAMEGRID_DETAILS) return merge();
    if (loading) return;
    const asset = window.GAMEGRID_CATALOG_MANIFEST?.detailsAsset;
    if (!/^details\.[a-f0-9]{16}\.js$/.test(asset || '')) return;
    loading = true;
    const script = document.createElement('script');
    script.src = `./${asset}`;
    script.onload = () => { loading = false; merge(); };
    script.onerror = () => { loading = false; };
    document.head.append(script);
  }
  document.addEventListener('click', event => {
    if (event.target.closest('.result,.cell.solved,.answer-cell,.valid-answer')) load();
  });
})();
